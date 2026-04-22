@echo off
echo Cleaning old build files...
if exist "build" rmdir /s /q "build"
if exist "InventoryManagerDebug.spec" del /q "InventoryManagerDebug.spec"

echo Installing requirements...
python -m pip install -r requirements.txt
python -m pip install pyinstaller

echo Building Windows Executable with CONSOLE (Debug Mode)...
python -m PyInstaller --clean --noconfirm --onefile --console --add-data ".env;." --name "InventoryManagerDebug" --distpath "." main.py
echo Build Complete! The final EXE (InventoryManagerDebug.exe) is now in this same folder.
pause
