from __future__ import print_function
from setuptools import setup, find_packages
from glob import glob
import os

here = os.path.dirname(os.path.abspath(__file__))
is_repo = os.path.exists(os.path.join(here, ".git"))

from distutils import log

log.set_verbosity(log.DEBUG)
log.info("setup.py entered")
log.info("$PATH=%s", os.environ["PATH"])

LONG_DESCRIPTION = "An extension to render cadquery objects in JupyterLab via pythreejs"

setup_args = {
    "name": "jupyter_cadquery",
    "version": "2.0.0-rc1",
    "description": "An extension to render cadquery objects in JupyterLab via pythreejs",
    "long_description": LONG_DESCRIPTION,
    "include_package_data": True,
    "data_files": [
        (
            "share/jupyter/nbextensions/jupyter_cadquery",
            glob("jupyter_cadquery/icons/*.png"),
        ),
    ],
    "install_requires": [
        "jupyterlab~=3.0",
        "ipywidgets~=7.6",
        "webcolors==1.11.1",
        "notebook~=6.2",
        "sidecar==0.5.0",
        "jupyter-cadquery-widgets~=2.0",
        "pythreejs~=2.3",
    ],
    "extras_require": {
        "dev": {"jupyter-packaging", "cookiecutter", "twine", "bumpversion", "black", "pylint", "pyYaml"}
    },
    "packages": find_packages(exclude=("jupyter_cadquery_widgets",)),
    "zip_safe": False,
    "author": "Bernhard Walter",
    "author_email": "b_walter@arcor.de",
    "url": "https://github.com/bernhard-42/jupyter-cadquery",
    "keywords": [
        "ipython",
        "jupyter",
        "widgets",
    ],
    "classifiers": [
        "Development Status :: 4 - Beta",
        "Framework :: IPython",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Multimedia :: Graphics",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
}

setup(**setup_args)
