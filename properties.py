"""
Properties for the RC Metrics add-on.
This module handles all property definitions.
"""

import bpy
from bpy.props import (StringProperty, BoolProperty, FloatProperty, 
                      EnumProperty, IntProperty, CollectionProperty, PointerProperty)
from bpy.types import PropertyGroup

class RCCamera(PropertyGroup):
    """Camera item for the RC Metrics UI list"""
    enabled: BoolProperty(
        name="Enable",
        description="Include this camera in metrics calculation",
        default=True
    )
    
    name: StringProperty(
        name="Name",
        description="Camera name",
        default=""
    )
    
    psnr: FloatProperty(
        name="PSNR",
        description="Peak Signal-to-Noise Ratio",
        default=0.0,
        precision=2
    )
    
    ssim: FloatProperty(
        name="SSIM",
        description="Structural Similarity Index",
        default=0.0,
        precision=4
    )
    
    has_results: BoolProperty(
        name="Has Results",
        description="Whether this camera has calculated results",
        default=False
    )
    
    is_problematic: BoolProperty(
        name="Is Problematic",
        description="Whether this camera has values below threshold",
        default=False
    )

class RCMETRICS_UL_CamerasList(bpy.types.UIList):
    """UI List for RC Camera selection"""
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            row.prop(item, "enabled", text="")
            
            # Show camera name
            split = row.split(factor=0.6)
            split.label(text=item.name)
            
            # Show metrics if available
            if item.has_results:
                # Use colored text based on thresholds
                if item.is_problematic:
                    # Red for problematic values
                    psnr_text = f"PSNR: {item.psnr:.2f}"
                    ssim_text = f"SSIM: {item.ssim:.4f}"
                    split.label(text=psnr_text, icon='ERROR')
                    split.label(text=ssim_text, icon='ERROR')
                else:
                    # Green for good values
                    psnr_text = f"PSNR: {item.psnr:.2f}"
                    ssim_text = f"SSIM: {item.ssim:.4f}"
                    split.label(text=psnr_text, icon='CHECKMARK')
                    split.label(text=ssim_text, icon='CHECKMARK')
            else:
                split.label(text="Not calculated")
                
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.prop(item, "enabled", text="")
            layout.label(text=item.name)

class RCMetricsProperties(PropertyGroup):
    """Property group for RC Metrics add-on"""
    rc_folder: StringProperty(
        name="RC Result Folder",
        description="Path to the RealityCapture result folder",
        default="",
        subtype='DIR_PATH'
    )
    
    metrics_output: StringProperty(
        name="Metrics Output",
        description="Path to save the metrics results",
        default="",
        subtype='DIR_PATH'
    )
    
    # Camera list and selection
    cameras: CollectionProperty(type=RCCamera)
    active_camera_index: IntProperty(default=0)
    
    # Rendering options
    save_renders: BoolProperty(
        name="Save Renders",
        description="Save rendered images to disk",
        default=True
    )
    
    render_quality: EnumProperty(
        name="Render Quality",
        description="Quality settings for rendering",
        items=[
            ('preview', "Preview", "Fast, low-quality rendering (32 samples)"),
            ('medium', "Medium", "Balanced rendering (64 samples)"),
            ('high', "High", "High-quality rendering (128 samples)"),
            ('final', "Final", "Production-quality rendering (256 samples)"),
        ],
        default='preview'
    )
    
    # Threshold settings
    psnr_threshold: FloatProperty(
        name="PSNR Threshold",
        description="Minimum acceptable PSNR value",
        default=30.0,
        min=0.0,
        soft_max=50.0
    )
    
    ssim_threshold: FloatProperty(
        name="SSIM Threshold",
        description="Minimum acceptable SSIM value",
        default=0.9,
        min=0.0,
        max=1.0
    )
    
    # Calculation progress
    is_calculating: BoolProperty(default=False)
    calculation_progress: FloatProperty(default=0.0, min=0.0, max=100.0)
    current_camera: StringProperty(default="")
    
    # Results
    has_results: BoolProperty(default=False)
    average_psnr: FloatProperty(default=0.0)
    average_ssim: FloatProperty(default=0.0)

# Registration function
def register():
    bpy.utils.register_class(RCCamera)
    bpy.utils.register_class(RCMETRICS_UL_CamerasList)
    bpy.utils.register_class(RCMetricsProperties)
    
    # Register property group
    bpy.types.Scene.rc_metrics = PointerProperty(type=RCMetricsProperties)

# Unregistration function
def unregister():
    # Unregister property group
    del bpy.types.Scene.rc_metrics
    
    bpy.utils.unregister_class(RCMetricsProperties)
    bpy.utils.unregister_class(RCMETRICS_UL_CamerasList)
    bpy.utils.unregister_class(RCCamera)
