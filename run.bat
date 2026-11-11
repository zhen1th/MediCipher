@echo off
title MediCipher - Medical Data Encryption and Security System
echo =======================================================
echo MEDICIPHER - MEDICAL DATA ENCRYPTION AND SECURITY SYSTEM
echo =======================================================
echo Menyiapkan lingkungan dan menjalankan aplikasi...

:: Tentukan interpreter Python (.venv jika ada, atau python sistem)
if exist ".venv\Scripts\python.exe" (
    echo Menggunakan Virtual Environment (.venv)...
    set "PYTHON_CMD=.venv\Scripts\python.exe"
) else (
    python --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Python tidak ditemukan di PATH sistem.
        echo Silakan pasang Python 3.10+ terlebih dahulu.
        pause
        exit /b 1
    )
    set "PYTHON_CMD=python"
)

:: Jalankan aplikasi utama
%PYTHON_CMD% main.py

if %errorlevel% neq 0 (
    echo.
    echo Aplikasi MediCipher dihentikan dengan kode keluar: %errorlevel%
    pause
)

