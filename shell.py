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

    """
    def __init__(self,cmd:str,root:bool=False,server:str='',listen:bool=False,keyfile:str='',user:str=''):        
        self.iter = listen
        self.__cmd = cmd
        self.__root = root
        self.shell = True
        self.__root_cmd = '''ssh -i  {user_key} {user}@{server} "sudo su root -c '{cmd}'"'''.format(**{
            "user_key":keyfile,
            "user":user,
            'server': server,
            "cmd":self.__cmd
        })
        pass
    def __enter__(self):
        """
        Description of __enter__

        Args:
            self (undefined):

        """
        if self.__root:
            self.process = subprocess.Popen(self.__root_cmd, encoding='utf-8',universal_newlines=True, shell=self.shell, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,text=True)
        else:
            self.process = subprocess.Popen(self.__cmd, encoding='utf-8',universal_newlines=True, shell=self.shell, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,text=True)
        
        if self.iter:
            # print('Self iter')
            # self.lines = str(self.process.stdout.read()).split('\n')
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
            pass
            # os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
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
with cmd('ls',server='tc-web-app1-bri.telmate.cc',keyfile='./mykeyfile',user='root') as cmd:
    print(cmd)
______________________________________________________________________________________________    

Iteration
______________________________________________________________________________________________

with cmd('ls',server='my-server.telmate.cc',listen=True,keyfile='./infra2016',user='root') as cmd:
    for result in cmd:
        print(result)
______________________________________________________________________________________________            
        
        """)




    pass
