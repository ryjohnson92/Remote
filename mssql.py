import pymssql,time
class connection:
    """
        Handles connecting to mysql database
    """
    def __init__(self,host:str='',user:str='',password:str='',database:str='',port:int=3306,trust_server:bool=True):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.trust_server = True
        self.conn,self.cur = self.__try_connect__()
        
    def __enter__(self):
        self.query()
        return self.cur.fetchall()
    
    def __exit__(self,a,b,c):
        try: 
            self.cur.close()
            self.conn.close()
        except Exception as err:
            print(err)
        
    def __try_connect__(self):
        for _ in range(3):
            try: 
                dbcon = pymssql.connect(self.host,self.user,self.password,self.database)
                return dbcon,dbcon.cursor()
            except Exception as err:
                print(err)
                time.sleep(5)
    @staticmethod
    def deps():
        return [
            "apt-get install --yes --no-install-recommends"
            "apt-transport-https",
            "build-essential",
            "curl",
            "gnupg",
            "unixodbc-dev",
            "unixodbc",
            "libpq-dev",
            "openssl",
            "g++",
            "freetds-dev",
            "freetds-bin",
            "tdsodbc",
            "libkrb5-dev",
            "-----------",
            "curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -",
            "curl https://packages.microsoft.com/config/ubuntu/22.04/prod.list > /etc/apt/sources.list.d/mssql-release.list",
            "apt-get update",
            "ACCEPT_EULA=Y apt-get install -y msodbcsql18",
            "ACCEPT_EULA=Y apt-get install -y mssql-tools18",
            """echo 'export PATH="$PATH:/opt/mssql-tools18/bin"' >> ~/.bashrc"""
        ]
    @staticmethod
    def install_cert():
        return '''openssl s_client -connect {server}:443 -showcerts </dev/null 2>/dev/null | sed -e '/-----BEGIN/,/-----END/!d' | tee "/usr/local/share/ca-certificates/ca.crt" >/dev/null && \
update-ca-certificates'''
    @staticmethod
    def help():
        print("""See deps() and install_cert(), goodluck""")
