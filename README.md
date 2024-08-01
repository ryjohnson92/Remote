# Remote Module

Making life easier since 2023!
This module will aid in properly executing remote SSH commands against remote hosts. 


## Usage/Examples

### Remote.shell
#### Simple
```python
from Remote.shell import cmd
with cmd('ls',server='server.my.com',keyfile='./myrootkey',user='root') as cmd:
    print(cmd)
```
#### Iteration
```python
from Remote.shell import cmd
with cmd('ls',server='server.my.com',listen=True,keyfile='./myrootkey',user='root') as cmd:
    for result in cmd:
        print(result)
```
### Remote.mysql

#### Simple
The following uses the subclass init function to pass credentials
```python
from Remote.mysql import connection
class my_query(connection):
    def __init__(self, payload):
        super().__init__(payload,'192.168.255.255','your_user','your_password')
    def query(self):
        self.cur.execute('select * from MyDB.MyTable limit 10')
        return self.cur.fetchall()

with my_query('') as results:
    print(results)
```
#### Supercession
The following examples use a child class to assign credentials, if you are using this multiple
times or for multiple connection / query types this is often the best usage.
```python
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
```