"""
Root conftest.py for photon_transport_code.

Adds this directory to sys.path so pytest can find the `transport` package
regardless of where it is invoked from (VS Code, command line, etc.).
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
