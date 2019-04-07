jupyter-cadquery
===============================

An extension to render cadquery objects in JupyterLab via pythreejs

Installation
------------

To install use pip:

    $ pip install jupyter_cadquery
    $ jupyter nbextension enable --py --sys-prefix jupyter_cadquery


For a development installation (requires npm),

    $ git clone https://github.com/bernhard-42/jupyter-cadquery.git
    $ cd jupyter-cadquery
    $ pip install -e .
    $ jupyter nbextension install --py --symlink --sys-prefix jupyter_cadquery
    $ jupyter nbextension enable --py --sys-prefix jupyter_cadquery
