"""
Render operators for RC Metrics Add-on.
"""

import bpy
import os
import numpy as np

class RCMETRICS_OT_RenderCompare(bpy.types.Operator):
    """Compare the current render slot with the original camera image"""
    bl_idname = "rcmetrics.render_compare"
    bl_label = "Compare with Original"
    bl_options = {'REGISTER', 'UNDO'}
    
    def check_active_camera(self, context):
        """Check if there is an active camera in the scene"""
        if not context.scene.camera:
            self.report({'ERROR'}, "No active camera. Please select a camera first!")
            return False, None
        
        # Check if the camera has a background image assigned
        cam_data = context.scene.camera.data
        has_bg_image = False
        bg_image = None
        
        if hasattr(cam_data, 'background_images') and cam_data.background_images:
            for bg in cam_data.background_images:
                if bg.image:
                    has_bg_image = True
                    bg_image = bg.image
                    break
        
        if not has_bg_image:
            self.report({'ERROR'}, "Active camera does not have a background image assigned")
            return False, None
            
        return True, bg_image
    
    def get_render_result(self, context):
        """Get render result from Render Slot 1 (after F12 was pressed)"""
        try:
            # Check for Render Result image
            if 'Render Result' not in bpy.data.images:
                self.report({'ERROR'}, "No Render Result found. Please render first by pressing F12.")
                return None
                
            render_result = bpy.data.images['Render Result']
            
            # Create a numpy array from the render result
            width = render_result.size[0]
            height = render_result.size[1]
            
            # Ensure we have valid dimensions
            if width <= 0 or height <= 0:
                self.report({'ERROR'}, f"Invalid render dimensions: {width}x{height}")
                return None
                
            # Get pixel data
            self.report({'INFO'}, f"Getting pixel data from render result ({width}x{height})...")
            
            # Check if pixels are available
            if not render_result.has_data:
                self.report({'ERROR'}, "Render Result has no data. Please render first by pressing F12.")
                return None
                
            pixels = np.array(render_result.pixels[:])
            
            if len(pixels) == 0:
                self.report({'ERROR'}, "Render result contains no pixel data")
                return None
                
            # Reshape the flat array to a 2D image with RGBA channels
            pixels = pixels.reshape((height, width, 4))
            self.report({'INFO'}, f"Successfully got render result with shape {pixels.shape}")
            
            # Convert to 8-bit RGB for comparison with original images
            pixels_rgb = (pixels[:, :, :3] * 255).astype(np.uint8)
            return pixels_rgb
            
        except Exception as e:
            import traceback
            self.report({'ERROR'}, f"Error getting render result: {str(e)}")
            traceback.print_exc()
            return None
    
    def calculate_metrics(self, render_array, original_image):
        """Calculate PSNR and SSIM between rendered image and original image"""
        try:
            # Import necessary modules
            import cv2
            from skimage.metrics import structural_similarity as ssim
            from skimage.metrics import peak_signal_noise_ratio as psnr
            
            # Ensure render array is valid
            if render_array is None or render_array.size == 0:
                self.report({'ERROR'}, "Render array is empty or None")
                return None, None
                
            # Get original image path
            original_path = bpy.path.abspath(original_image.filepath)
            self.report({'INFO'}, f"Original image path: {original_path}")
            
            if not os.path.exists(original_path):
                self.report({'ERROR'}, f"Original image not found: {original_path}")
                return None, None
                
            # Load original image using OpenCV
            original_img = cv2.imread(original_path)
            
            if original_img is None:
                self.report({'ERROR'}, f"Failed to load original image: {original_path}")
                return None, None
                
            # Log image dimensions
            self.report({'INFO'}, f"Original image shape: {original_img.shape}")
            self.report({'INFO'}, f"Rendered image shape: {render_array.shape}")
            
            # Resize original image if dimensions don't match
            if original_img.shape[:2] != render_array.shape[:2]:
                self.report({'INFO'}, f"Resizing original image from {original_img.shape[:2]} to {render_array.shape[:2]}")
                original_img = cv2.resize(original_img, (render_array.shape[1], render_array.shape[0]))
            
            # Convert render array from RGB to BGR for comparison with OpenCV's BGR format
            render_bgr = cv2.cvtColor(render_array, cv2.COLOR_RGB2BGR)
            
            # Convert to grayscale for SSIM calculation
            original_gray = cv2.cvtColor(original_img, cv2.COLOR_BGR2GRAY)
            rendered_gray = cv2.cvtColor(render_bgr, cv2.COLOR_BGR2GRAY)
            
            # Calculate metrics
            psnr_value = psnr(original_img, render_bgr)
            ssim_value = ssim(original_gray, rendered_gray)
            
            self.report({'INFO'}, f"Calculated metrics - PSNR: {psnr_value:.2f}dB, SSIM: {ssim_value:.4f}")
            
            return psnr_value, ssim_value
            
        except Exception as e:
            import traceback
            self.report({'ERROR'}, f"Error calculating metrics: {str(e)}")
            traceback.print_exc()
            return None, None
    
    def execute(self, context):
        try:
            # Check if we have active camera with background image
            camera_ok, bg_image = self.check_active_camera(context)
            if not camera_ok:
                return {'CANCELLED'}
            
            # Get existing render result (doesn't perform new rendering)
            self.report({'INFO'}, "Getting existing render result from Render Slot 1...")
            render_array = self.get_render_result(context)
            if render_array is None:
                self.report({'ERROR'}, "No render result found. Please render first by pressing F12.")
                return {'CANCELLED'}
            
            # Calculate metrics
            self.report({'INFO'}, "Comparing render result with original camera image...")
            psnr_value, ssim_value = self.calculate_metrics(render_array, bg_image)
            
            if psnr_value is not None and ssim_value is not None:
                # Store results in scene properties
                context.scene.rc_metrics.last_psnr = psnr_value
                context.scene.rc_metrics.last_ssim = ssim_value
                
                # Report success
                self.report({'INFO'}, f"Image comparison complete - PSNR: {psnr_value:.2f}dB, SSIM: {ssim_value:.4f}")
                return {'FINISHED'}
            else:
                self.report({'ERROR'}, "Failed to calculate image metrics")
                return {'CANCELLED'}
                
        except Exception as e:
            import traceback
            self.report({'ERROR'}, f"Unexpected error: {str(e)}")
            traceback.print_exc()
            return {'CANCELLED'}

# Registration
def register():
    bpy.utils.register_class(RCMETRICS_OT_RenderCompare)

def unregister():
    bpy.utils.unregister_class(RCMETRICS_OT_RenderCompare)
