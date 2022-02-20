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
    "version": "3.0.0rc4",
    "description": "An extension to render cadquery objects in JupyterLab via pythreejs",
    "long_description": LONG_DESCRIPTION,
    "include_package_data": True,
    "python_requires": ">=3.6",
    "install_requires": [
        "webcolors~=1.11",
        "jupyterlab~=3.2",
        "voila~=0.3",
        "cadquery_massembly~=0.9",
        "pyquaternion~=0.9.9",
        "cad-viewer-widget~=1.0.0",
    ],
    "extras_require": {
        "dev": {"jupyter-packaging", "cookiecutter", "twine", "bumpversion", "black", "pylint", "pyYaml"},
        "prod": {"cadquery==master"},
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
