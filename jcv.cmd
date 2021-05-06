@echo off

set cmd=python -c "import os, jupyter_cadquery.viewer.server as c; print(os.path.dirname(c.__file__))"
for /f %%i in (' %cmd% ') do set viewer_path=%%i
voila %viewer_path%\viewer.ipynb