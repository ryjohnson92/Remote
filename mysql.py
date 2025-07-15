import mysql.connector

class connection:
    """
        Handles connecting to mysql database
    """
    def __init__(self,payload,host:str='',user:str='',password:str='',port:int=3306):
        self._host = host
        self._user = user
        self._pwd = password
        self._port = port
        self.payload = payload
        
    def __enter__(self):
        try:
            self.conn = mysql.connector.connect(
                host=self._host,
                user=self._user,
                password=self._pwd,
                port=self._port
            )
            self.conn.autocommit = True
            self.cur = self.conn.cursor(buffered=True)
            self._results = self.query()
            return self._results
        except mysql.connector.Error as err:
            self._results = None 
            raise 
        except Exception as err:
            self._results = None
            raise       

    def call_proc(self,proc,args=[]):
        try:
            self.cur.callproc(proc,args)
            results = []
            for result in self.cur.stored_results():
                result = result.fetchall()
                for item in result:
                    results.append(item)              
            return results
        except Exception as err:
            print(err)
            print('^^ {}'.format(proc))
            
    def __exit__(self,a,b,c):
        try: 
            self.cur.close()
            self.conn.close()
        except: pass
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.cur:
            try:
                self.cur.close()
            except mysql.connector.Error as err:
                print(f"Error closing cursor: {err}")
            self.cur = None
        if self.conn:
            try:
                self.conn.close()
            except mysql.connector.Error as err:
                print(f"Error closing connection: {err}")
            self.conn = None
        return False
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
