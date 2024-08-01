# Remote Module

Making life easier since 2023!
This module will aid in properly executing remote SSH commands against remote hosts. 


## Usage/Examples

### Simple
```python
from Remote.shell import cmd
with cmd('ls',server='server.my.com',keyfile='./myrootkey',user='root') as cmd:
    print(cmd)
```
### Iteration
```python
with cmd('ls',server='server.my.com',listen=True,keyfile='./myrootkey',user='root') as cmd:
    for result in cmd:
        print(result)
```