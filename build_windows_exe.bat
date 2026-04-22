@echo off
echo Cleaning old build files...
if exist "build" rmdir /s /q "build"
if exist "InventoryManager.spec" del /q "InventoryManager.spec"

echo Installing requirements...
python -m pip install -r requirements.txt
python -m pip install pyinstaller

echo Building Windows Executable (Single File)...
python -m PyInstaller --clean --noconfirm --onefile --windowed --add-data ".env;." --name "InventoryManager" --distpath "." main.py
echo Build Complete! The final EXE (InventoryManager.exe) is now in this same folder.
pause
