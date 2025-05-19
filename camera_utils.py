"""
Camera utilities for the RC Metrics add-on.
This module handles camera selection, display, and management.
"""

import bpy
from bpy.props import BoolProperty, StringProperty, FloatProperty
from bpy.types import PropertyGroup, UIList

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

class RCMETRICS_UL_CamerasList(UIList):
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

def find_rc_cameras(context, collection_name=None):
    """Find all cameras that match RC naming pattern"""
    rc_cameras = []
    
    for obj in bpy.data.objects:
        if obj.type == 'CAMERA':
            # Check for typical RC camera names (starts with C followed by numbers)
            if obj.name.startswith('C') and '_DSC' in obj.name and obj.name.endswith('.png'):
                rc_cameras.append(obj)
            # Or check if it's in the specified collection
            elif collection_name and obj.users_collection and collection_name in [c.name for c in obj.users_collection]:
                rc_cameras.append(obj)
    
    return rc_cameras

def update_camera_list(context):
    """Update the camera list with all available RC cameras"""
    rc_metrics = context.scene.rc_metrics
    
    # Clear current list
    rc_metrics.cameras.clear()
    
    # Find all RC cameras
    cameras = find_rc_cameras(context)
    
    # Populate the list
    for cam in cameras:
        item = rc_metrics.cameras.add()
        item.name = cam.name
        item.enabled = True
        item.has_results = False
        
    # Set the active camera index
    if len(rc_metrics.cameras) > 0:
        rc_metrics.active_camera_index = 0
    else:
        rc_metrics.active_camera_index = -1
    
    return len(rc_metrics.cameras)

def select_all_cameras(context, select=True):
    """Select or deselect all cameras in the list"""
    rc_metrics = context.scene.rc_metrics
    
    for cam in rc_metrics.cameras:
        cam.enabled = select
    
    return len(rc_metrics.cameras)

def get_enabled_cameras(context):
    """Get a list of camera objects that are enabled in the UI"""
    rc_metrics = context.scene.rc_metrics
    enabled_cameras = []
    
    for cam_item in rc_metrics.cameras:
        if cam_item.enabled:
            # Find the actual camera object
            cam_obj = bpy.data.objects.get(cam_item.name)
            if cam_obj and cam_obj.type == 'CAMERA':
                enabled_cameras.append(cam_obj)
    
    return enabled_cameras

def update_camera_results(context, camera_name, psnr, ssim, threshold_psnr=30.0, threshold_ssim=0.9):
    """Update the results for a specific camera"""
    rc_metrics = context.scene.rc_metrics
    
    for i, cam_item in enumerate(rc_metrics.cameras):
        if cam_item.name == camera_name:
            cam_item.psnr = psnr
            cam_item.ssim = ssim
            cam_item.has_results = True
            
            # Mark as problematic if below thresholds
            cam_item.is_problematic = (psnr < threshold_psnr or ssim < threshold_ssim)
            
            # Update the active camera index to show this camera
            rc_metrics.active_camera_index = i
            break
