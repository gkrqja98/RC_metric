"""
Example usage script for testing outside of Blender.
This is for development purposes only.
"""

import os
import sys
import cv2
import numpy as np
from skimage.metrics import structural_similarity, peak_signal_noise_ratio

def test_calculate_metrics(ref_img_path, comp_img_path):
    """
    Calculate PSNR and SSIM between two images.
    For testing purposes.
    """
    # Read images
    ref_img = cv2.imread(ref_img_path)
    comp_img = cv2.imread(comp_img_path)
    
    if ref_img is None:
        print(f"Error: Could not read reference image: {ref_img_path}")
        return None, None
    
    if comp_img is None:
        print(f"Error: Could not read comparison image: {comp_img_path}")
        return None, None
    
    # Resize if needed
    if ref_img.shape != comp_img.shape:
        comp_img = cv2.resize(comp_img, (ref_img.shape[1], ref_img.shape[0]))
    
    # Convert to grayscale for SSIM
    ref_gray = cv2.cvtColor(ref_img, cv2.COLOR_BGR2GRAY)
    comp_gray = cv2.cvtColor(comp_img, cv2.COLOR_BGR2GRAY)
    
    # Calculate metrics
    psnr = peak_signal_noise_ratio(ref_img, comp_img)
    ssim = structural_similarity(ref_gray, comp_gray)
    
    return psnr, ssim

def test_analyze_rc_folder(folder_path):
    """
    Analyze a RealityCapture result folder.
    For testing purposes.
    """
    if not os.path.exists(folder_path):
        print(f"Error: Folder does not exist: {folder_path}")
        return
    
    # Check for .abc file
    abc_files = [f for f in os.listdir(folder_path) if f.endswith('.abc')]
    if not abc_files:
        print("Error: No .abc file found in the folder")
        return
    
    # Check for image files
    png_files = [f for f in os.listdir(folder_path) if f.endswith('.png') and not f.endswith('_diffuse.png')]
    if len(png_files) < 2:
        print("Error: Not enough image files found in the folder")
        return
    
    # Check for texture file
    texture_files = [f for f in os.listdir(folder_path) if f.endswith('_diffuse.png')]
    if not texture_files:
        print("Warning: No texture file found")
    
    print("RealityCapture folder analysis:")
    print(f"- ABC file: {abc_files[0]}")
    print(f"- Image files: {len(png_files)} found")
    if texture_files:
        print(f"- Texture file: {texture_files[0]}")
    else:
        print("- Texture file: None found")
    
    return True

if __name__ == "__main__":
    # Example usage
    if len(sys.argv) > 1:
        rc_folder = sys.argv[1]
        print(f"Testing folder: {rc_folder}")
        test_analyze_rc_folder(rc_folder)
    else:
        print("Usage: python test_standalone.py <rc_folder_path>")
        print("Example: python test_standalone.py D:/Cursor/01_RealityCapture_Result")
