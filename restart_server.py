import subprocess
import signal
import os

# Stop the current server
try:
    # Find and stop Django server
    result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], capture_output=True, text=True)
    lines = result.stdout.split('\n')

    # Look for Django server process
    for line in lines:
        if 'python.exe' in line and (line.find('manage.py') != -1 or line.find('runserver') != -1):
            # Extract PID and kill
            parts = line.split()
            if len(parts) >= 2:
                pid = parts[1]
                try:
                    os.kill(int(pid), signal.CTRL_BREAK_EVENT)
                    print(f"Killed process {pid}")
                except:
                    pass
except Exception as e:
    print(f"Error stopping server: {e}")

# Start the server again
print("Restarting Django server...")
subprocess.Popen(['python', 'manage.py', 'runserver'], creationflags=subprocess.CREATE_NEW_CONSOLE)
