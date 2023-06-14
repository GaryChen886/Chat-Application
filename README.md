# Chat-Application
111-2 COMPUTER NETWORKS HW
## Setup
- Define your port on chat_server.py
  - If the port was occupied, try ```netstat -ano | findstr <port>``` to get further info
  - The message should be like this ```TCP    127.0.0.1:<port>         0.0.0.0:0              LISTENING       <PID>```
  - Use ```taskkill /F /PID <PID>``` to force stop the task
## Get started
- Enter the following commands on two terminal pages respectively:
  -  ```python3 chat_server.py```
  -  ```python3 chat_app.py```
- Open the Windows Command Prompt and enter the following command:
  - ```telnet localhost <port>```
  
