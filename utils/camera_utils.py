"""
Camera utilities for the RC Metrics add-on.
This module handles camera selection, display, and management.
"""

import bpy
from bpy.props import BoolProperty, StringProperty, FloatProperty
from bpy.types import PropertyGroup, UIList

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
        item.enabled = False  # Start with all disabled
        item.has_results = False
        
    # Set the active camera index
    if len(rc_metrics.cameras) > 0:
        rc_metrics.active_camera_index = 0
    else:
        rc_metrics.active_camera_index = -1
    
    return len(rc_metrics.cameras)

def select_single_camera(context, index):
    """Select only one camera by index"""
    rc_metrics = context.scene.rc_metrics
    
    # Deselect all cameras first
    for cam in rc_metrics.cameras:
        cam.enabled = False
    
    # Select only the specified camera
    if 0 <= index < len(rc_metrics.cameras):
        rc_metrics.cameras[index].enabled = True
        rc_metrics.active_camera_index = index
        return rc_metrics.cameras[index].name
    
    return None

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
    
    # Debug print to help troubleshoot
    print(f"Updating results for camera: {camera_name}")
    print(f"Values: PSNR={psnr:.2f}, SSIM={ssim:.4f}")
    
    found = False
    for i, cam_item in enumerate(rc_metrics.cameras):
        if cam_item.name == camera_name:
            cam_item.psnr = psnr
            cam_item.ssim = ssim
            cam_item.has_results = True
            
            # Mark as problematic if below thresholds
            cam_item.is_problematic = (psnr < threshold_psnr or ssim < threshold_ssim)
            
            # Update the active camera index to show this camera
            rc_metrics.active_camera_index = i
            found = True
            print(f"Updated camera {camera_name} with PSNR={psnr:.2f}, SSIM={ssim:.4f}")
            break
    
    if not found:
        print(f"WARNING: Camera {camera_name} not found in the list!")
        print(f"Available cameras: {[cam.name for cam in rc_metrics.cameras]}")
    
    # Force a redraw of all UI areas
    for area in context.screen.areas:
        area.tag_redraw()
    
    return found
