"""
Render utilities for the RC Metrics add-on.
This module handles rendering and render settings.
"""

import bpy
import os
import numpy as np

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
    
    print(f"Rendering from camera: {camera.name}")
    
    # Store original resolution and filepath
    original_filepath = scene.render.filepath
    original_resolution_x = scene.render.resolution_x
    original_resolution_y = scene.render.resolution_y
    
    # Adjust resolution to match camera's background image, if any
    if camera.data.background_images and camera.data.background_images[0].image:
        bg_img = camera.data.background_images[0].image
        scene.render.resolution_x = bg_img.size[0]
        scene.render.resolution_y = bg_img.size[1]
        print(f"Setting render resolution to match background: {bg_img.size[0]}x{bg_img.size[1]}")
    
    # If we're saving the render
    if output_path:
        # Set output path for this render
        scene.render.filepath = output_path
        print(f"Saving render to: {output_path}")
        # Render and save
        bpy.ops.render.render(write_still=True)
    else:
        # Render without saving
        scene.render.filepath = ""
        print("Rendering without saving to disk")
        bpy.ops.render.render()
    
    # Get the render result
    render_result = None
    if bpy.data.images.get('Render Result'):
        render_img = bpy.data.images['Render Result']
        print(f"Got render result: {render_img.size[0]}x{render_img.size[1]}")
        
        # Check if the image size is valid
        if render_img.size[0] > 0 and render_img.size[1] > 0 and len(render_img.pixels) > 0:
            try:
                # Convert render to numpy array
                width, height = render_img.size
                # Make sure we have enough pixels
                expected_pixels = width * height * 4  # RGBA format
                if len(render_img.pixels) >= expected_pixels:
                    render_result = np.array(render_img.pixels[:]).reshape(
                        (height, width, 4))
                    # Convert from RGBA to BGR (OpenCV format)
                    render_result = render_result[:, :, :3][:, :, ::-1]
                    # Convert from float [0,1] to uint8 [0,255]
                    render_result = (render_result * 255).astype(np.uint8)
                    print(f"Converted render to numpy array, shape: {render_result.shape}")
                else:
                    print(f"Error: Expected {expected_pixels} pixels but got {len(render_img.pixels)}")
            except Exception as e:
                print(f"Error converting render to numpy array: {e}")
                render_result = None
        else:
            print(f"Error: Invalid render image size or no pixels: {render_img.size[0]}x{render_img.size[1]}, pixels: {len(render_img.pixels)}")
    else:
        print("No 'Render Result' found after rendering")
    
    # Try loading the output image directly if we saved it and failed to get render result
    if render_result is None and output_path and os.path.exists(output_path):
        print(f"Trying to load rendered image from disk: {output_path}")
        try:
            import cv2
            render_result = cv2.imread(output_path)
            if render_result is not None:
                print(f"Successfully loaded rendered image from disk, shape: {render_result.shape}")
        except Exception as e:
            print(f"Error loading rendered image from disk: {e}")
    
    # Restore original settings
    scene.render.filepath = original_filepath
    scene.render.resolution_x = original_resolution_x
    scene.render.resolution_y = original_resolution_y
    
    return render_result

def get_camera_background_image(camera):
    """Get the background image for a camera as a numpy array"""
    try:
        import cv2
        
        print(f"Getting background image for camera: {camera.name}")
        
        if not camera.data.background_images:
            print(f"No background images for camera {camera.name}")
            return None
            
        if not camera.data.background_images[0].image:
            print(f"Background image not set for camera {camera.name}")
            return None
        
        bg_img = camera.data.background_images[0].image
        
        # Get full path to the image
        if not bg_img.filepath:
            print(f"No filepath for background image in camera {camera.name}")
            return None
            
        # Convert relative path to absolute
        filepath = bpy.path.abspath(bg_img.filepath)
        print(f"Background image path: {filepath}")
        
        # Check if file exists
        if not os.path.exists(filepath):
            print(f"Background image file does not exist: {filepath}")
            return None
            
        # Load image using OpenCV
        img = cv2.imread(filepath)
        if img is None:
            print(f"Failed to load image: {filepath}")
            return None
            
        print(f"Successfully loaded background image for {camera.name}, shape: {img.shape}")
        return img
        
    except ImportError:
        print("Could not import OpenCV. Please install required dependencies.")
        return None
    except Exception as e:
        print(f"Error loading background image for {camera.name}: {e}")
        return None

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
