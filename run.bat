@echo off
echo === Cash3 / Pick3 Lottery Analyzer ===
echo.

:: Install dependencies if needed
pip show flask >nul 2>&1 || (
    echo Installation des dependances...
    pip install -r requirements.txt
)

echo Demarrage du serveur...
echo Ouvrez votre navigateur sur: http://localhost:5000
echo.
python app.py
pause
