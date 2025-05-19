"""
Properties for the RC Metrics add-on.
This module handles all property definitions.
"""

import bpy
from bpy.props import (StringProperty, BoolProperty, PointerProperty)
from bpy.types import PropertyGroup

class RCImportProperties(PropertyGroup):
    """Simplified property group for RC Metrics add-on"""
    rc_folder: StringProperty(
        name="RC Result Folder",
        description="Path to the RealityCapture result folder",
        default="",
        subtype='DIR_PATH'
    )

# Registration function
def register():
    bpy.utils.register_class(RCImportProperties)
    
    # Register property group
    bpy.types.Scene.rc_metrics = PointerProperty(type=RCImportProperties)

# Unregistration function
def unregister():
    # Unregister property group
    del bpy.types.Scene.rc_metrics
    
    bpy.utils.unregister_class(RCImportProperties)
