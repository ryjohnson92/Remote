import re,time,asyncio,os,paramiko,socket,select
from Local.shell import cmd as L_cmd
from threading import Thread,Event
from Remote.shell import cmd as rs_cmd
from Remote.shell import scp as rs_scp
from contextlib import ExitStack


TUNNEL_GLOBAL_TIMEOUT = int(os.environ.get('REMOTE_HOST_TUNNEL_GLOBAL_TIMEOUT_SECONDS', '30'))
TUNNEL_GLOBAL_PING_INT = int(os.environ.get('REMOTE_HOST_TUNNEL_GLOBAL_PING_INT', '5'))

class host:
    class ssh_tunnel:
        bw_compat = dict(pubkeys=["rsa-sha2-512", "rsa-sha2-256"])
        class SSHConnectionManager(Thread):
            """
            Manages the lifecycle of the SSH connection.
            Establishes the connection and provides the Paramiko Transport object.
            """
            def __init__(self, host, port, username, password_or_key_path,bw_compat=[]):
                super().__init__()
                self.host = host
                self.port = port
                self.username = username
                self.password_or_key_path = password_or_key_path
                self._stop_event = Event()
                self._connection_ready_event = Event()
                self._transport = None
                self._ssh_client = None
                self.daemon = True 
                self.bw_compat = bw_compat

            def run(self):
                try:
                    self._ssh_client = paramiko.SSHClient()
                    self._ssh_client.load_system_host_keys()
                    self._ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    if os.path.exists(str(self.password_or_key_path)) and os.path.isfile(str(self.password_or_key_path)):
                        self._ssh_client.connect(
                            hostname=self.host,
                            port=self.port,
                            username=self.username,
                            key_filename=self.password_or_key_path,
                            timeout=TUNNEL_GLOBAL_TIMEOUT,
                            disabled_algorithms=self.bw_compat
                        )
                    else:
                        self._ssh_client.connect(
                            hostname=self.host,
                            port=self.port,
                            username=self.username,
                            password=self.password_or_key_path,
                            timeout=TUNNEL_GLOBAL_TIMEOUT,
                            disabled_algorithms=self.bw_compat
                        )
                    self._transport = self._ssh_client.get_transport()
                    if not self._transport.is_active():
                        raise Exception("SSH transport is not active after connection.")
                    self._connection_ready_event.set()
                    while not self._stop_event.is_set() and self._transport.is_active():
                        time.sleep(1)
                except paramiko.AuthenticationException:
                    print("[SSHManager] Authentication failed. Check credentials.")
                except paramiko.SSHException as e:
                    print(f"[SSHManager] SSH connection error: {e}")
                except socket.error as e:
                    print(f"[SSHManager] Socket error during connection: {e}")
                except Exception as e:
                    print(f"[SSHManager] An unexpected error occurred: {e}")
                finally:
                    self._connection_ready_event.clear()
                    if self._ssh_client:
                        self._ssh_client.close()

            def get_transport(self):
                """Returns the Paramiko Transport object, blocks until ready."""
                self._connection_ready_event.wait()
                return self._transport

            def stop(self):
                """Signals the SSHConnectionManager to terminate."""
                self._stop_event.set()
                if self._transport and self._transport.is_active():
                    self._transport.close() # Attempt to close transport if active

        class LocalPortForwarder(Thread):
            """
            Listens on a local port and forwards incoming connections
            through the provided Paramiko Transport to a remote target.
            """
            def __init__(self, local_bind_address, local_port, remote_target_host, remote_target_port, transport):
                super().__init__()
                self.local_bind_address = local_bind_address
                self.local_port = local_port
                self.remote_target_host = remote_target_host
                self.remote_target_port = remote_target_port
                self.transport = transport
                self.daemon = True 
                self._stop_event = Event()
                self._server_socket = None

            def _handle_client_connection(self, client_socket, client_addr):
                """Handle a single client connection through the tunnel."""
                remote_channel = None 
                try:
                    remote_channel = self.transport.open_channel(
                        "direct-tcpip",
                        (self.remote_target_host, self.remote_target_port),
                        client_socket.getpeername() 
                    )
                    if remote_channel is None:
                        client_socket.close()
                        return
                    while not self._stop_event.is_set():
                        rlist = []
                        if client_socket: rlist.append(client_socket)
                        if remote_channel: rlist.append(remote_channel) 
                        if not rlist: break
                        readable, _, _ = select.select(rlist, [], [], TUNNEL_GLOBAL_PING_INT)

                        if self._stop_event.is_set(): break

                        if client_socket in readable:
                            data = client_socket.recv(4096)
                            if len(data) == 0: break 
                            remote_channel.send(data)

                        if remote_channel in readable:
                            data = remote_channel.recv(4096)
                            if len(data) == 0: break 
                            client_socket.send(data)

                except socket.error as e:
                    print(f"[Forwarder] Socket error in handler for {client_addr}: {e}")
                except Exception as e:
                    print(f"[Forwarder] General error in handler for {client_addr}: {e}")
                finally:
                    for _ in (remote_channel,client_socket):
                        try:
                            _.close()
                        except (EOFError, socket.timeout):
                            pass
            def run(self):
                """Starts the local listening socket for incoming connections."""
                try:
                    self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, TUNNEL_GLOBAL_PING_INT)
                    self._server_socket.bind((self.local_bind_address, self.local_port))
                    self._server_socket.listen(5)
                    while not self._stop_event.is_set():
                        self._server_socket.settimeout(0.5)
                        try:
                            client_socket, addr = self._server_socket.accept()
                        except socket.timeout:
                            continue 
                        except OSError as e:
                            if self._stop_event.is_set():
                                break
                            raise TimeoutError("Tunnel Could not start up")
                        client_handler = Thread(
                            target=self._handle_client_connection, args=(client_socket, addr), daemon=True
                        )
                        client_handler.start()

                except Exception as e:
                    print(e)
                finally:
                    if self._server_socket:
                        self._server_socket.close()

            def stop(self):
                """Signals the LocalPortForwarder to stop and close its listening socket."""
                self._stop_event.set()
                if self._server_socket:
                    try:
                        self._server_socket.shutdown(socket.SHUT_RDWR)
                        self._server_socket.close()
                    except OSError:
                        pass 

        def __init__(self,host:str,local_port,remote_port,ssh_key:str,ssh_user:str,jump_host:str,bw_compat:bool=False):
            """
            Creates a tunnel to a remote host.

            Args:
                host (str): The remote host to port foward.
                local_port (int): Local port to occupy
                remote_port (int): Remote port to forward
                ssh_key [dir path](str): Where to find the SSH key for the host
                ssh_user (str): User to login to remote host as
                jump_host (str): Jump host
                stop_event (Event): Event to trigger stopping 

            Returns:
                int: The product of a and b.
            """
            self.host = host
            self.local_port = str(local_port)
            self.remote_port = str(remote_port)
            self.ssh_key = ssh_key
            self.ssh_user = ssh_user
            self.jump_host = jump_host
            self.READY_EVENT = Event()
            self.bw_compat = bw_compat

        def __enter__(self):
            LOCAL_BIND_ADDRESS = '127.0.0.1'
            with ExitStack() as stack:
                config = self.get_ssh_config(self.jump_host)
                stack.callback(self._cleanup)
                self.ssh_manager = self.SSHConnectionManager(config.get("hostname", self.jump_host), int(config.get("port", 22)), config.get("user",self.ssh_user), os.path.expanduser(config.get("identityfile", [self.ssh_key])[0]),self.bw_compat)
                
                self.ssh_manager.start()
                ssh_transport = self.ssh_manager.get_transport()
                if ssh_transport and ssh_transport.is_active():
                    self.forwarder = self.LocalPortForwarder(
                        LOCAL_BIND_ADDRESS,
                        int(self.local_port),
                        self.host,
                        int(self.remote_port),
                        ssh_transport
                    )
                    self.forwarder.start()
                else: raise TimeoutError("Tunnel Did not start")
                stack.pop_all()
            return self
        
        def __exit__(self,a,b,c):
            self._cleanup()

        def _cleanup(self):
            if self.forwarder and self.forwarder.is_alive():
                self.forwarder.stop()
                self.forwarder.join(timeout=5)
                if self.forwarder.is_alive():
                    print("[Main] WARNING: LocalPortForwarder did not join within timeout!")
            if self.ssh_manager and self.ssh_manager.is_alive():
                self.ssh_manager.stop()
                self.ssh_manager.join(timeout=10)
                if self.ssh_manager.is_alive():
                    print("[Main] WARNING: SSHConnectionManager did not join within timeout!")

        def get_ssh_config(self,hostname):
            config = paramiko.SSHConfig()
            try:
                with open(os.path.expanduser("~/.ssh/config"), "r") as f:
                    config.parse(f)
            except FileNotFoundError:
                return {}
            return config.lookup(hostname)

    def __init__(self,server,keyfile,user):
        self.server = server
        self.keyfile = keyfile
        self.user = user
        self.is_reachable = self.__self_reachable__
        self.ping_peer = self.__self_ping_peer__
    
    def tunnel(self,remote_host,remote_port,local_port,bw_compat)->tuple:
        return self.ssh_tunnel(
            remote_host,
            local_port,
            remote_port,
            self.keyfile,
            self.user,
            self.server,
            bw_compat
        )

    def cmd(self,cmd,ssh_flags:dict={},listen:bool=False,root:bool=False):
        return rs_cmd(cmd=cmd,root=root,server=self.server,keyfile=self.keyfile,user=self.user,ssh_flags=ssh_flags,listen=listen)

    def scp(self,local_path,remote_path,ssh_flags:dict={}):
        return rs_scp(local_path,remote_path,self.server, keyfile=self.keyfile,user=self.user,ssh_flags=ssh_flags)

    def __bool__(self):
        return self.__self_reachable__()
    #################### reachable  #################################################
    def __self_reachable__(self):
        return self.__reachable__(self.server,self.keyfile,self.user)

    @staticmethod
    def is_reachable(server:str,keyfile:str,user:str):
        return host.__reachable__(server,keyfile,user)

    @staticmethod
    def __reachable__(server:str,keyfile:str,user:str)->bool:
        """ Attempts to connect to the host to ensure it is connectable"""
        try:
            with rs_cmd("hostname",True,server,keyfile=keyfile,user=user) as hostname:
                assert str(hostname).find(server) ==0 , 'Could not connect to server'
            return True
        except Exception as err:
            print(err) 
            return False
    ################################################################################
    #################### Ping Peer  ################################################
    def __self_ping_peer__(self,peer:str):
        return host.__ping_peer__(peer,self.server,self.keyfile,self.user)

    @staticmethod
    def ping_peer(peer:str,server:str,keyfile:str,user:str)->bool:
        return host.__ping_peer__(peer,server,keyfile,user)

    @staticmethod
    def __ping_peer__(peer:str,server:str,keyfile:str,user:str)->bool:
        """ Pings host based on @peer param from a remote host"""
        with rs_cmd("ping -c 1 -W 2 {}".format(peer),server=server,keyfile=keyfile,user=user,root=True) as F:           
            speed = re.findall(r'time=(\d{1,10000}[.]?\d{0,6}) ms',F)
            speed = float(speed[0]) if len(speed) > 0 else None
            speed = None if not speed else 0 if speed < 200 else 1 if speed < 450 else 2
            return not len(re.findall(r'.*(100% packet loss).*',F)) > 0
