"""
Operators module for RC Metrics Add-on.
This module handles registration of all operators.
"""

from . import import_operators
from . import camera_operators
from . import metrics_operators
from . import export_operators

def register():
    """Register all operators"""
    import_operators.register()
    camera_operators.register()
    metrics_operators.register()
    export_operators.register()

def unregister():
    """Unregister all operators"""
    export_operators.unregister()
    metrics_operators.unregister()
    camera_operators.unregister()
    import_operators.unregister()
