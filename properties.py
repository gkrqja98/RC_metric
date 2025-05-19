"""
Properties for the RC Metrics add-on.
"""

import bpy
from bpy.props import (StringProperty, PointerProperty)
from bpy.types import PropertyGroup

from bpy.props import (StringProperty, PointerProperty, FloatProperty, EnumProperty)

def get_camera_items(self, context):
    """Get all camera objects for enum property"""
    cameras = [(cam.name, cam.name, f"Use camera {cam.name}") for cam in context.scene.objects if cam.type == 'CAMERA']
    # Add 'None' option
    if not cameras:
        cameras = [('None', 'No Cameras', 'No cameras in scene')]
    return cameras

def update_active_camera(self, context):
    """Update the active camera when selection changes"""
    if self.selected_camera and self.selected_camera != 'None':
        # Find the camera object
        camera = context.scene.objects.get(self.selected_camera)
        if camera and camera.type == 'CAMERA':
            context.scene.camera = camera
    return None

def get_diff_view_modes(self, context):
    """Get modes for difference view"""
    return [
        ('HEATMAP', 'Heatmap', 'Display difference as a heatmap'),
        ('GRAYSCALE', 'Grayscale', 'Display difference in grayscale'),
        ('COLORIZED', 'Colorized', 'Display difference with color enhancement')
    ]

class RCMetricsProperties(PropertyGroup):
    """Property group for RC Metrics add-on"""
    rc_folder: StringProperty(
        name="RC Result Folder",
        description="Path to the RealityCapture result folder",
        default="",
        subtype='DIR_PATH'
    )
    
    # Camera selection property
    selected_camera: EnumProperty(
        name="Camera",
        description="Select camera for rendering and comparison",
        items=get_camera_items,
        update=update_active_camera
    )
    
    # Properties to store image comparison results
    last_psnr: FloatProperty(
        name="Last PSNR",
        description="Peak Signal-to-Noise Ratio from last comparison",
        default=0.0,
        precision=2
    )
    
    last_ssim: FloatProperty(
        name="Last SSIM",
        description="Structural Similarity Index from last comparison",
        default=0.0,
        min=0.0,
        max=1.0,
        precision=4
    )
    
    # Difference image view options
    diff_view_mode: EnumProperty(
        name="Difference View Mode",
        description="How to display the difference image",
        items=[
            ('HEATMAP', 'Heatmap', 'Display difference as a heatmap'),
            ('GRAYSCALE', 'Grayscale', 'Display difference in grayscale'),
            ('COLORIZED', 'Colorized', 'Display difference with color enhancement')
        ],
        default='COLORIZED'
    )
    
    diff_multiplier: FloatProperty(
        name="Difference Multiplier",
        description="Multiply the difference values to make subtle differences more visible",
        default=5.0,
        min=1.0,
        max=20.0
    )

# Registration function
def register():
    bpy.utils.register_class(RCMetricsProperties)
    
    # Register property group
    bpy.types.Scene.rc_metrics = PointerProperty(type=RCMetricsProperties)

# Unregistration function
def unregister():
    # Unregister property group
    del bpy.types.Scene.rc_metrics
    
    bpy.utils.unregister_class(RCMetricsProperties)
