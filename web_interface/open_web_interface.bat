@echo off
echo Opening Thought Agent Web Interface...
echo The application should be running at http://localhost:5000
echo.

REM Open the default browser to the web interface
start http://localhost:5000

echo.
echo If the page doesn't load, make sure the Flask server is running by executing:
echo start_web_interface.bat
echo.
pause
