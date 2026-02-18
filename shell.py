import subprocess
class cmd:
    """
        Allows for remote execution of simple or complex commands
        Args:
            cmd (str): The command string to execute
            root (bool): execute as root?
            server (str): Server to execute command on
            Listen (bool): Creates / allows for iteration!
            keyfile (str): Path to key file
            user (str): user to enter remote device as 
            ssh_flags (dict): pass additional flags to ssh flag:value

    """
    def __init__(self,cmd:str,root:bool=False,server:str='',listen:bool=False,keyfile:str='',user:str='',ssh_flags:dict={}):        
        self.iter = listen
        self.__cmd = cmd
        self.__root = root
        self.shell = True
        assert type(ssh_flags) == dict,'Must pass dict object with flag:value'
        self.flags = [f"{x} {ssh_flags[x]}" for x in ssh_flags]
        self.__cmd = f"""ssh -i {keyfile} {" ".join(self.flags)} {user}@{server} "{cmd if not self.__root else f"sudo {cmd}"}" """
        pass
    def __enter__(self):
        """
        Description of __enter__

        Args:
            self (undefined):

        """
        self.process = subprocess.Popen(self.__cmd, encoding='utf-8',universal_newlines=True, shell=self.shell, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,text=True)
        if self.iter:
            return self
        else:
            text = self.process.stdout.read()
            retcode = self.process.wait()
            return text

    def __iter__(self):
        while True:
            line = self.process.stdout.readline()
            if not line:
                break
            yield line.rstrip()
        pass
    def __exit__(self,a,b,c):
        try:
            self.process.terminate() # If it times out, send SIGTERM
            self.process.wait()
        except Exception as err:
            print(err)
        pass
    
    @staticmethod
    def help():
        print("""
Shell Command Module! 
==============================================================================================
Making life easier since 2023!
This module will aid in properly executing remote SSH commands. 
==============================================================================================
Consider the following usage example!
______________________________________________________________________________________________

Simple usage
______________________________________________________________________________________________

from Remote_Connection.shell import cmd
with cmd('ls',server='webapp1',keyfile='./mykeyfile',user='root') as cmd:
    print(cmd)
______________________________________________________________________________________________    

Iteration
______________________________________________________________________________________________

with cmd('ls',server='my-server.',listen=True,keyfile='./infra2016',user='root') as cmd:
    for result in cmd:
        print(result)
______________________________________________________________________________________________            
        
        """)




    pass
    
class scp(cmd):
    def __init__(self,local_path,remote_path,server:str='',keyfile:str='',user:str='',ssh_flags:dict={}):
        super().__init__("",True,server,False,keyfile,user,{})
        self.flags = [f"{x} {ssh_flags[x]}" for x in ssh_flags]
        self.__root_cmd = f"scp {''.join(self.flags)} -i {keyfile}  {local_path} {user}@{server}:{remote_path}"
    pass

    def __enter__(self):
        try:
            self.process = subprocess.Popen(self.__root_cmd, encoding='utf-8',universal_newlines=True, shell=self.shell, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,text=True)
            text = self.process.stdout.read()
            retcode = self.process.wait()
            return True
        except Exception as err:
            print(err)
            return False
