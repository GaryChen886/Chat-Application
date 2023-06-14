import subprocess


subprocess.run(['taskkill', '/F', '/PID', '8888'])


server_process = subprocess.Popen(['python3', 'chat_server.py'])


client_process = subprocess.Popen(['python3', 'chat_client.py'])


server_process.wait()
client_process.wait()

print("Done")
