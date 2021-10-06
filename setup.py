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
    "version": "2.2.1",
    "description": "An extension to render cadquery objects in JupyterLab via pythreejs",
    "long_description": LONG_DESCRIPTION,
    "include_package_data": True,
    "python_requires": ">=3.6",
    "install_requires": [
        "ipywidgets~=7.6",
        "webcolors~=1.11",
        "notebook~=6.3",
        "sidecar~=0.5",
        "jupyter-cadquery-widgets~=2.0",
        "pythreejs~=2.3",
        "voila~=0.2",
        "cadquery_massembly~=0.9",
        "orbitcontrol-patch~=0.1.0",
        "pyquaternion~=0.9.9",
    ],
    "extras_require": {
        "dev": {"jupyter-packaging", "cookiecutter", "twine", "bumpversion", "black", "pylint", "pyYaml"},
        "prod": {"cadquery==2.1"},
    },
    "packages": find_packages(),
    "scripts": ["jcv", "jcv.cmd"],
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
