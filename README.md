# P2P File Sharing App

USER MANUAL:

1. Place "client.py" and "ui.py" files in the same foler

2. First run "server.py", your computer IP address and PORT will be shown on the terminal like this:

Server begin listening on YOUR_IP:YOUR_PORT.

The default PORT is 60000, you may also want to change your port if you want at line 6 in "server.py" file

```python 
PORT = YOUR_PORT
```

3. Change your server's IP address and PORT at line 359 and 369 in "client.py" file

```python 
# change to server IP address if you want to connect to other machine
IP = YOUR_IP
PORT = YOUR_PORT
```

4. Run "ui.py" to start the program!
