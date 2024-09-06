import mysql.connector

class connection:
    """
        Handles connecting to mysql database
    """
    def __init__(self,payload,host:str='',user:str='',password:str='',port:int=3306):
        self.conn = mysql.connector.connect(
            host=host ,
            user=user,
            password=password,
            port= port
        )
        self.conn.autocommit = True
        self.cur = self.conn.cursor()
        self.payload = payload
        
    def __enter__(self):
        return self.query()
    
    def __exit__(self,a,b,c):
        try: 
            self.cur.close()
            self.conn.close()
        except: pass

    @staticmethod
    def help():
        print("""
MYSQL Connection Module! 
==============================================================================================
A context manager implementation of mysql-connector!
==============================================================================================
Consider the following usage example!
______________________________________________________________________________________________

Simple usage
The following uses the subclass init function to pass credentials
______________________________________________________________________________________________

from Remote.mysql import connection
class my_query(connection):
    def __init__(self, payload):
        super().__init__(payload,'192.168.255.255','your_user','your_password')
    def query(self):
        self.cur.execute('select * from MyDB.MyTable limit 10')
        return self.cur.fetchall()

with my_query('') as results:
    print(results)
______________________________________________________________________________________________    

Supercession
The following examples use a child class to assign credentials, if you are using this multiple
times or for multiple connection / query types this is often the best usage.
______________________________________________________________________________________________

from Remote.mysql import connection

class my_local_connection(connection):
    def __init__(self, payload):
        super().__init__(payload,'192.168.255.255','your_user','your_password')
    pass

class my_query(my_local_connection):
    def query(self):
        self.cur.execute('select * from MyDB.MyTable limit 10')
        return self.cur.fetchall()

class my_second_query(my_local_connection):
    def query(self):
        self.cur.execute('select * from MyDB.MySecondTable limit 10')
        return self.cur.fetchall()

with my_query('') as results:
    print(results)

with my_second_query('') as results:
    print(results)
______________________________________________________________________________________________            
""")

        pass
