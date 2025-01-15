from Remote.shell import cmd

class host:
    @staticmethod
    def is_reachable(server:str,keyfile:str,user:str):
        try:
            with ssh_connection("hostname",True,server,keyfile=keyfile,user=user) as hostname:
                assert str(hostname).find(server) ==0 , 'Could not connect to server'
            return True
        except: 
            return False
