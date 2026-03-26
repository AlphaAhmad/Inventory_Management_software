@echo off
echo Installing requirements...
pip install -r requirements.txt
pip install pyinstaller

echo Building Windows Executable (Single File)...
pyinstaller --noconfirm --onefile --windowed --add-data ".env;." --name "InventoryManager" main.py

echo Build Complete! Check the /dist folder for the final EXE.
pause
