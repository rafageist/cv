@echo off
REM Script to generate CV using WeasyPrint with GTK4

REM Configure environment variables for GTK4
set "GTK_PATH=D:\apps\gtk4"
set "PATH=%GTK_PATH%\bin;%PATH%"
set "GI_TYPELIB_PATH=%GTK_PATH%\lib\girepository-1.0"
set "XDG_DATA_DIRS=%GTK_PATH%\share"

REM Execute the Python script
python scripts\build_cv.py

pause
