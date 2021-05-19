import nbformat
import json
import sys

with open(sys.argv[1], "r") as fd:
    nb = json.load(fd)

try:
    nbformat.validate(nb)
    print("==> OK")
except:
    print("==> ERROR")
