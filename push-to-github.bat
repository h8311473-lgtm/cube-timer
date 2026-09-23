@echo off
rem ============================================================
rem  推送魔方计时器到 GitHub（自动等待代理就绪 + 自动重试）
rem  用法：双击本文件
rem ============================================================
cd /d "%~dp0"

set "PROXY=http://127.0.0.1:7897"
set /a TRY=0
set /a MAX=40

echo ============================================
echo   推送 cube-timer 到 GitHub
echo   代理: %PROXY%  （若你的端口不同，改本文件第 8 行）
echo ============================================
echo.

:waitproxy
set /a TRY+=1
if %TRY% GTR %MAX% goto :noproxy

powershell -NoProfile -Command "if ((Test-NetConnection 127.0.0.1 -Port 7897 -WarningAction SilentlyContinue).TcpTestSucceeded) { exit 0 } else { exit 1 }"
if errorlevel 1 (
    echo [%TRY%/%MAX%] 等待代理就绪... 请打开你的代理软件并连接
    timeout /t 3 /nobreak >nul
    goto :waitproxy
)

echo 代理已就绪，开始推送...
echo.
git config --global http.proxy  "%PROXY%"
git config --global https.proxy "%PROXY%"

git push origin main
if errorlevel 1 (
    echo.
    echo ------------------------------------------------------------
    echo  推送失败。
    echo  · 若提示用户名/密码：请在弹出窗口里完成 GitHub 登录
    echo    （走完浏览器授权后不要关闭窗口，等它自己结束）
    echo  · 若提示连接失败：检查代理是否还开着，然后重新双击本文件
    echo ------------------------------------------------------------
    pause
    exit /b 1
)

echo.
echo ============================================
echo   校验：下面两行前 7 位应完全一致
echo ============================================
git rev-parse HEAD
git ls-remote origin main
echo.
echo 一致（例如都是 5b6839f）即推送成功。
echo 仓库地址：https://github.com/h8311473-lgtm/cube-timer
pause
exit /b 0

:noproxy
echo.
echo 等了 %MAX% 次仍未检测到代理（127.0.0.1:7897）。
echo  1. 请先打开代理软件并连接
echo  2. 如果端口不是 7897，用记事本打开本文件改第 8 行
echo  3. 然后重新双击本文件
echo.
pause
exit /b 1
