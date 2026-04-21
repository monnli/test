@echo off
REM 一键初始化数据库 + 写入完整演示数据（Windows）
REM 用法：双击运行，或在 cmd 中执行 scripts\init_demo.bat

setlocal enabledelayedexpansion
chcp 65001 > nul
cd /d %~dp0..

echo.
echo ============================================================
echo   青苗守护者 · 一键初始化（Windows）
echo ============================================================
echo.

echo [1/3] 创建数据库与所有表...
python scripts\init_db.py
if errorlevel 1 (
    echo.
    echo [ERROR] 数据库初始化失败，请检查：
    echo   1. MySQL 是否正在运行
    echo   2. .env 中的 MYSQL_USER / MYSQL_PASSWORD 是否正确
    pause
    exit /b 1
)

echo.
echo [2/3] 写入基础数据（学校 / 班级 / 学生 / 教师 / 16 个演示账号）...
python scripts\seed_demo_data.py
if errorlevel 1 (
    echo [ERROR] 基础数据写入失败
    pause
    exit /b 1
)

echo.
echo [3/5] 写入增强演示数据（量表 / 文本 / 对话 / 成绩 / 课堂 / 时序 / 预警）...
python scripts\seed_demo_extras.py
if errorlevel 1 (
    echo [ERROR] 增强数据写入失败
    pause
    exit /b 1
)

echo.
echo [4/5] 合成 5 段演示课堂视频（storage\demo_videos\）...
python scripts\generate_demo_videos.py
if errorlevel 1 (
    echo [WARN] 演示视频合成失败（可忽略，需先装 opencv-python 和 Pillow）
)

echo.
echo [5/5] 创建摄像头 + 课表（2026 春季学期）...
python scripts\seed_cameras_and_schedules.py
if errorlevel 1 (
    echo [WARN] 摄像头/课表 seed 失败（可忽略）
)

echo.
echo ============================================================
echo   初始化完成！
echo.
echo   下一步：双击 scripts\start_all.bat 启动所有服务
echo   或手动启动：
echo     - cd backend ^&^& python run.py
echo     - cd ai_service ^&^& python server.py
echo     - cd frontend ^&^& npm run dev
echo.
echo   浏览器访问：http://localhost:5173
echo   默认账号：  admin / admin123
echo ============================================================
echo.
pause
