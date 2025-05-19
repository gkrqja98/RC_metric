"""
UI components for the RC Metrics add-on.
"""

from . import main_panel
from . import camera_panel
from . import metrics_panel

def register():
    """Register all UI components"""
    main_panel.register()
    camera_panel.register()
    metrics_panel.register()

def unregister():
    """Unregister all UI components"""
    metrics_panel.unregister()
    camera_panel.unregister()
    main_panel.unregister()
