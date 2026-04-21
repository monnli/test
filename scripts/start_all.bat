@echo off
REM 一键启动青苗守护者所有服务（Windows）
REM 用法：双击或在 cmd 中执行 scripts\start_all.bat

setlocal
chcp 65001 > nul
cd /d %~dp0..
set PROJECT_ROOT=%CD%

REM ========== conda 环境配置 ==========
REM 默认环境名 kt_env，可通过 .env 中 CONDA_ENV=xxx 覆盖
set CONDA_ENV=kt_env
if exist ".env" (
    for /f "tokens=2 delims==" %%A in ('findstr /B "CONDA_ENV=" .env 2^>nul') do set CONDA_ENV=%%A
)

REM 找 Anaconda/Miniconda 安装路径
set CONDA_HOOK=
if exist "%USERPROFILE%\Anaconda3\Scripts\activate.bat" set CONDA_HOOK=%USERPROFILE%\Anaconda3\Scripts\activate.bat
if exist "%USERPROFILE%\miniconda3\Scripts\activate.bat" set CONDA_HOOK=%USERPROFILE%\miniconda3\Scripts\activate.bat
if exist "C:\ProgramData\Anaconda3\Scripts\activate.bat" set CONDA_HOOK=C:\ProgramData\Anaconda3\Scripts\activate.bat
if exist "C:\ProgramData\Miniconda3\Scripts\activate.bat" set CONDA_HOOK=C:\ProgramData\Miniconda3\Scripts\activate.bat

if "%CONDA_HOOK%"=="" (
    echo [WARN] 未找到 Anaconda/Miniconda 安装路径，子窗口将使用系统默认 Python
    echo        如需使用 conda 环境 %CONDA_ENV%，请手动在各子窗口先执行：conda activate %CONDA_ENV%
    set ACTIVATE_CMD=
) else (
    echo 使用 conda 环境：%CONDA_ENV%（激活脚本：%CONDA_HOOK%）
    set ACTIVATE_CMD=call "%CONDA_HOOK%" %CONDA_ENV% ^&^&
)

if not exist logs mkdir logs

echo.
echo ==========================================
echo   青苗守护者 · 一键启动
echo ==========================================
echo.

echo [1/3] 启动 AI 推理服务（http://localhost:8000）
start "qingmiao-ai" cmd /k "cd /d %PROJECT_ROOT%\ai_service && %ACTIVATE_CMD% python server.py"

timeout /t 3 /nobreak > nul

echo [2/3] 启动 Flask 后端（http://localhost:5000）
start "qingmiao-backend" cmd /k "cd /d %PROJECT_ROOT%\backend && %ACTIVATE_CMD% python run.py"

timeout /t 3 /nobreak > nul

echo [3/3] 启动前端开发服务器（http://localhost:5173）
start "qingmiao-frontend" cmd /k "cd /d %PROJECT_ROOT%\frontend && npm run dev"

echo.
echo ==========================================
echo   全部启动完成！
echo.
echo   数据大屏：http://localhost:5173/dashboard
echo   工作台：  http://localhost:5173/workbench
echo   账号：    admin / admin123
echo.
echo   每个服务在单独的 cmd 窗口中运行
echo   关闭对应窗口即可停止该服务
echo ==========================================
echo.
pause
endlocal
