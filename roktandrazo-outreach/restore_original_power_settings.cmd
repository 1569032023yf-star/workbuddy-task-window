@echo off
REM Restore Original Power Settings
REM Restores power scheme from backup and reverts all Delivery Guard changes

setlocal
cd /d "%~dp0"

set BACKUP_DIR=output\power_diagnostics
set BACKUP_FILE=%BACKUP_DIR%\original_power_scheme_backup.pow

echo ============================================
echo   RESTORE ORIGINAL POWER SETTINGS
echo ============================================
echo.
echo This will restore the HP Optimized power plan
echo to its state before Delivery Guard modifications.
echo.
echo Backup file: %BACKUP_FILE%
echo.

if not exist "%BACKUP_FILE%" (
    echo [ERROR] Backup file not found: %BACKUP_FILE%
    echo No changes to restore.
    pause
    exit /b 1
)

echo [ACTION] Restoring power scheme from backup...
powercfg /import "%BACKUP_FILE%" fb5220ff-7e1a-47aa-9a42-50ffbf45c673 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to import power scheme.
    echo The scheme may already exist. Try using the .pow file directly:
    echo   1. Open Control Panel ^> Power Options
    echo   2. Create a new power plan
    echo   3. Import the .pow file
    pause
    exit /b 1
)

echo [OK] Power scheme restored from backup.

REM Activate the restored scheme
powercfg /setactive fb5220ff-7e1a-47aa-9a42-50ffbf45c673
echo [OK] Restored scheme activated.

echo.
echo ============ RESTORE COMPLETE ==============
echo.
echo Current settings restored:
echo   - Sleep after: original value
echo   - Hibernate after: original value
echo   - Hybrid sleep: original value
echo   - Wake timers: original value
echo.
echo Verify with: powercfg /query SCHEME_CURRENT
echo.

endlocal
