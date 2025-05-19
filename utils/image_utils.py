"""
Image processing utilities for the RC Metrics add-on.
This module handles image calculations and metrics.
"""

import numpy as np

def calculate_image_metrics(ref_img, rendered_img):
    """
    Calculate PSNR and SSIM between two numpy arrays (images).
    ref_img and rendered_img are expected to be BGR numpy arrays.
    """
    try:
        import cv2
        from skimage.metrics import structural_similarity, peak_signal_noise_ratio
        
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

def load_image(image_path):
    """Load an image from path using OpenCV"""
    try:
        import cv2
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")
        return image
    except ImportError:
        print("OpenCV (cv2) is not installed. Please install the required dependencies.")
        return None
    except Exception as e:
        print(f"Error loading image {image_path}: {e}")
        return None

def save_image(image, output_path):
    """Save an image to disk using OpenCV"""
    try:
        import cv2
        directory = os.path.dirname(output_path)
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        result = cv2.imwrite(output_path, image)
        if not result:
            raise ValueError(f"Failed to save image to {output_path}")
        return True
    except ImportError:
        print("OpenCV (cv2) is not installed. Please install the required dependencies.")
        return False
    except Exception as e:
        print(f"Error saving image to {output_path}: {e}")
        return False

def create_visualization(ref_img, rendered_img, output_path=None):
    """Create a visual comparison between reference and rendered images"""
    try:
        import cv2
        import numpy as np
        
        # Ensure same dimensions
        if ref_img.shape != rendered_img.shape:
            rendered_img = cv2.resize(rendered_img, (ref_img.shape[1], ref_img.shape[0]))
        
        # Create a visual diff
        diff = cv2.absdiff(ref_img, rendered_img)
        diff_color = cv2.applyColorMap(diff, cv2.COLORMAP_JET)
        
        # Create side-by-side comparison
        h, w = ref_img.shape[:2]
        comparison = np.zeros((h, w * 3, 3), dtype=np.uint8)
        comparison[:, :w] = ref_img
        comparison[:, w:w*2] = rendered_img
        comparison[:, w*2:] = diff_color
        
        # Add labels
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(comparison, 'Reference', (10, 30), font, 1, (255, 255, 255), 2)
        cv2.putText(comparison, 'Rendered', (w + 10, 30), font, 1, (255, 255, 255), 2)
        cv2.putText(comparison, 'Difference', (w * 2 + 10, 30), font, 1, (255, 255, 255), 2)
        
        # Save if output path provided
        if output_path:
            save_image(comparison, output_path)
        
        return comparison
    except ImportError:
        print("OpenCV (cv2) is not installed. Please install the required dependencies.")
        return None
    except Exception as e:
        print(f"Error creating visualization: {e}")
        return None
