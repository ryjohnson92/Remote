import re

from Remote.shell import cmd as rs_cmd


class host:
     
    def __init__(self,server,keyfile,user):
        self.server = server
        self.keyfile = keyfile
        self.user = user
        self.is_reachable = self.__self_reachable__
        self.ping_peer = self.__self_ping_peer__

    def cmd(self,cmd):
        return rs_cmd(cmd,True,self.server,keyfile=self.keyfile,user=self.user)

    def __bool__(self):
        return __self_reachable__()
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