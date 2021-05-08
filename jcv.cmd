@echo off

if [%1]==[--port] goto :port
goto :viewer

:port
set ZMQ_PORT=%2
echo [JCV] Using port %ZMQ_PORT%

:viewer

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
voila --enable_nbextensions=True --VoilaExecutor.kernel_name=jcv %JCV_PATH%\viewer.ipynb
