@echo off
echo Starting Thought Agent Web Interface...
echo.

REM Navigate to the web interface directory
cd /d "%~dp0"

REM Activate the virtual environment
echo Activating virtual environment...
call "..\venv\Scripts\activate.bat"

REM Install requirements if needed
echo Installing/updating requirements...
pip install -r requirements.txt

REM Initialize ChromaDB
echo.
echo Initializing ChromaDB...
python initialize_chroma.py

REM Start the web application
echo.
echo Starting Flask application...
echo Access the application at: http://localhost:5000
echo Press Ctrl+C to stop the server
echo.

python app.py

pause
