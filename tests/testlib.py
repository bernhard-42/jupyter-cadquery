import pytest
import time
from PIL import Image, ImageChops
import numpy as np
import io
import sys

import ipywidgets
from IPython import get_ipython
from IPython.display import display

def list_approx(l1, l2):
    assert len(l1) == len(l2)
    for i, (x1,x2) in enumerate(zip(l1, l2)):
        assert abs((x1 - x2) / x2) < 0.01, f"Element {i} differs: {x1}, {x2}"


def save_test(cv, name):
    filename = f'{name.replace(" ", "_").lower()}.png'
    print(filename)
    cv.widget.test_func = None
    cv.export_png(filename)

    
class Test(object):
    def __init__(self, name, out, cv, compare=False):
        self.name = name
        self.out = out
        self.cv = cv
        self.compare = compare
        self.filename = f'{name.replace(" ", "_").lower()}.png'
 
    def __enter__(self):
        with self.out:
            print(f"Test '{self.name}'")
        
            if compare:
                self.cv.widget.test_func = compare(self.filename, self.out, self.cv)
            
    
    def __exit__(self, type, value, traceback):
        ...


def compare(filename, output, cv):
    def inner(data):
      
        img1 = Image.open(io.BytesIO(data))
        img2 = Image.open(filename)

        diff = ImageChops.difference(img1, img2).convert("RGB")

        values = np.array(diff)
        w,h,c = values.shape
        result = sum(values.flatten()) / (w*h*c)

        cv.widget.test_func = None
        
        with output:
            assert result < 0.1, f"Image diff is {result}"
            
    return inner

# Notebook execution stop

class NotebookExit(BaseException):
    pass

ipython = get_ipython()
_showtraceback = ipython._showtraceback

def _exception_handler(exception_type, exception, traceback):
    if exception_type == NotebookExit:
        print("Notebook paused: %s" % (exception), file=sys.stderr)
    else:
        _showtraceback(exception_type, exception, traceback)

ipython._showtraceback = _exception_handler

def stop(msg):
    raise NotebookExit(msg)
    
# Log output

out = ipywidgets.Output()

display(out)

with out:
    print("Test log:")