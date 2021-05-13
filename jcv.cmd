@echo off

set ZMQ_PORT=
set CAD_HEIGHT=
set CAD_WIDTH=
set THEME=light

:GETOPTS
if /I "%1" == "-p" set ZMQ_PORT=%2 & shift
if /I "%1" == "-h" set CAD_HEIGHT=%2 & shift
if /I "%1" == "-w" set CAD_WIDTH=%2 & shift
if /I "%1" == "-d" set THEME=dark
shift
if not "%1" == "" goto GETOPTS

echo [JCV] Creating a Jupyter kernel specification called 'jcv' for this conda environment
python -m ipykernel install --name jcv --display-name jcv

set JCV_PATH=%userprofile%\.jcv
set CMD=python -c "import os, jupyter_cadquery.viewer.server as c; print(os.path.dirname(c.__file__))"
for /f %%i in (' %CMD% ') do set VIEWER_PATH=%%i

echo [JCV] Copying the voila notebook to %JCV_PATH%
if not exist %JCV_PATH% mkdir %JCV_PATH%
copy %VIEWER_PATH%\viewer.ipynb %JCV_PATH%\

echo [JCV] Signing the voila notebook
jupyter trust %JCV_PATH%\viewer.ipynb

echo [JCV] Starting Jupyter CadQuery Viewer
voila --theme=%THEME% ^
    --enable_nbextensions=True ^
    --show_tracebacks=True ^
    --VoilaExecutor.kernel_name=jcv ^
    --VoilaConfiguration.file_whitelist="favicon.ico" ^
    --VoilaConfiguration.file_whitelist=".*\.js" ^
    %JCV_PATH%\viewer.ipynb

