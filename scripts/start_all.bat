@echo off
REM 一键启动青苗守护者所有服务（Windows）
REM 用法：双击或在 cmd 中执行 scripts\start_all.bat

cd /d %~dp0..
set PROJECT_ROOT=%CD%

if not exist logs mkdir logs

echo [1/3] 启动 AI 推理服务（http://localhost:8000）
start "qingmiao-ai" cmd /k "cd /d %PROJECT_ROOT%\ai_service && python server.py"

timeout /t 2 /nobreak > nul

echo [2/3] 启动 Flask 后端（http://localhost:5000）
start "qingmiao-backend" cmd /k "cd /d %PROJECT_ROOT%\backend && python run.py"

timeout /t 2 /nobreak > nul

echo [3/3] 启动前端开发服务器（http://localhost:5173）
start "qingmiao-frontend" cmd /k "cd /d %PROJECT_ROOT%\frontend && npm run dev"

echo.
echo ==========================================
echo   全部启动完成！
echo.
echo   数据大屏：http://localhost:5173/dashboard
echo   工作台：  http://localhost:5173/workbench
echo   账号：    admin / admin123
echo ==========================================
echo.
pause
