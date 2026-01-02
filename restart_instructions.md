# Django Server Restart Instructions

## Why Restart is Required
The 400 error persists because Django hasn't reloaded the updated code in `apps/chatbot/views.py`. The server needs to be restarted to pick up our logic order fixes and FFmpeg audio conversion.

## Restart Commands

### Method 1: Stop and Start
```bash
# Stop the current server (Ctrl+C in the terminal running the server)
# Then start again:
cd c:/Users/farha/Downloads/Graduation_project_ITI_Backend
python manage.py runserver
```

### Method 2: If server is running in background
```bash
# Find the process
tasklist | findstr python

# Kill the Django process (replace PID with actual process ID)
taskkill /PID [PID] /F

# Start fresh
cd c:/Users/farha/Downloads/Graduation_project_ITI_Backend
python manage.py runserver
```

### Method 3: Quick restart
```bash
# If using Windows
taskkill /IM python.exe /F
cd c:/Users/farha/Downloads/Graduation_project_ITI_Backend
python manage.py runserver
```

## Expected Result
After restart, when you test voice recording:
1. ✅ No more 400 errors
2. ✅ Audio will be processed correctly
3. ✅ Logic order fix will be active
4. ✅ FFmpeg conversion will work (if installed)

## If 400 Error Persists After Restart
1. Check Django console for error messages
2. Verify the updated code is loaded
3. Check if FFmpeg is installed (for enhanced audio processing)
