@echo off
cd /d "C:\Users\admin\.openclaw\workspace\modelhub"

:loop
echo [%date% %time%] Starting Python server on 18080...
start /b python -m http.server 18080 >nul 2>&1

echo [%date% %time%] Starting Pinggy tunnel...
ssh -o StrictHostKeyChecking=no -p 443 -R0:localhost:18080 -o ServerAliveInterval=30 a.pinggy.io 2>&1 | findstr /C:"run.pinggy"

echo [%date% %time%] Tunnel closed. Restarting in 3 seconds...
timeout /t 3 /nobreak >nul
goto loop
