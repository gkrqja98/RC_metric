"""
Render utilities for the RC Metrics add-on.
This module handles rendering and metric calculation.
"""

import bpy
import os
import numpy as np
import cv2
from skimage.metrics import structural_similarity, peak_signal_noise_ratio
import json
import time

def setup_render_settings(context, quality="preview"):
    """Setup render settings for evaluation"""
    scene = context.scene
    # Set render engine
    scene.render.engine = 'CYCLES'
    
    # Set render settings based on quality level
    if quality == "preview":
        scene.cycles.samples = 32
    elif quality == "medium":
        scene.cycles.samples = 64
    elif quality == "high":
        scene.cycles.samples = 128
    else:  # "final"
        scene.cycles.samples = 256
        
    # Keep resolution at 100% for accurate metrics
    scene.render.resolution_percentage = 100
    
    # Disable film transparency so we get just the render
    scene.render.film_transparent = False

def render_from_camera(context, camera, output_path=None):
    """
    Render the scene from a specific camera.
    If output_path is None, the render is not saved to disk.
    Returns the rendered image as a numpy array.
    """
    scene = context.scene
    scene.camera = camera
    
    # Store original filepath
    original_filepath = scene.render.filepath
    
    # If we're saving the render
    if output_path:
        # Set output path for this render
        scene.render.filepath = output_path
        # Render and save
        bpy.ops.render.render(write_still=True)
    else:
        # Render without saving
        scene.render.filepath = ""
        bpy.ops.render.render()
    
    # Get the render result
    render_result = None
    if bpy.data.images.get('Render Result'):
        render_img = bpy.data.images['Render Result']
        # Convert render to numpy array
        render_result = np.array(render_img.pixels[:]).reshape(
            (render_img.size[1], render_img.size[0], 4))
        # Convert from RGBA to BGR (OpenCV format)
        render_result = render_result[:, :, :3][:, :, ::-1]
        # Convert from float [0,1] to uint8 [0,255]
        render_result = (render_result * 255).astype(np.uint8)
    
    # Restore original filepath
    scene.render.filepath = original_filepath
    
    return render_result

def get_camera_background_image(camera):
    """Get the background image for a camera as a numpy array"""
    if camera.data.background_images and camera.data.background_images[0].image:
        bg_img = camera.data.background_images[0].image
        
        # Get full path to the image
        if bg_img.filepath:
            # Convert relative path to absolute
            filepath = bpy.path.abspath(bg_img.filepath)
            
            # Load image using OpenCV
            if os.path.exists(filepath):
                return cv2.imread(filepath)
    
    return None

def calculate_image_metrics(ref_img, rendered_img):
    """
    Calculate PSNR and SSIM between two numpy arrays (images).
    ref_img and rendered_img are expected to be BGR numpy arrays.
    """
    try:
        if ref_img is None or rendered_img is None:
            raise ValueError("One of the images is None")
            
        # Ensure same dimensions
        if ref_img.shape != rendered_img.shape:
            rendered_img = cv2.resize(rendered_img, (ref_img.shape[1], ref_img.shape[0]))
            
        # Convert to grayscale for SSIM
        ref_gray = cv2.cvtColor(ref_img, cv2.COLOR_BGR2GRAY)
        rendered_gray = cv2.cvtColor(rendered_img, cv2.COLOR_BGR2GRAY)
        
        # Calculate metrics
        psnr = peak_signal_noise_ratio(ref_img, rendered_img)
        ssim = structural_similarity(ref_gray, rendered_gray)
        
        return psnr, ssim
        
    except Exception as e:
        print(f"Error calculating metrics: {e}")
        return None, None

def update_metrics_summary(metrics_summary, camera_name, psnr, ssim):
    """Update the metrics summary with new camera results"""
    if "cameras" not in metrics_summary:
        metrics_summary["cameras"] = []
        
    # Add this camera's results
    metrics_summary["cameras"].append({
        "camera": camera_name,
        "psnr": psnr,
        "ssim": ssim
    })
    
    # Update min/max
    if "min_psnr" not in metrics_summary or psnr < metrics_summary["min_psnr"]:
        metrics_summary["min_psnr"] = psnr
    if "max_psnr" not in metrics_summary or psnr > metrics_summary["max_psnr"]:
        metrics_summary["max_psnr"] = psnr
        
    if "min_ssim" not in metrics_summary or ssim < metrics_summary["min_ssim"]:
        metrics_summary["min_ssim"] = ssim
    if "max_ssim" not in metrics_summary or ssim > metrics_summary["max_ssim"]:
        metrics_summary["max_ssim"] = ssim
        
    # Calculate new averages
    total_psnr = sum(cam["psnr"] for cam in metrics_summary["cameras"])
    total_ssim = sum(cam["ssim"] for cam in metrics_summary["cameras"])
    count = len(metrics_summary["cameras"])
    
    metrics_summary["average_psnr"] = total_psnr / count
    metrics_summary["average_ssim"] = total_ssim / count
    
    return metrics_summary
