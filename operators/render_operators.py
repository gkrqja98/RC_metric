"""
Render operators for RC Metrics Add-on.
"""

import bpy
import os
import numpy as np
import tempfile

class RCMETRICS_OT_RenderCompare(bpy.types.Operator):
    """Render the current camera view and compare with the original image"""
    bl_idname = "rcmetrics.render_compare"
    bl_label = "Render and Compare"
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
    
    def render_current_view(self, context):
        """Render the current view and return the render result"""
        try:
            # Store original render settings
            original_filepath = context.scene.render.filepath
            original_format = context.scene.render.image_settings.file_format
            
            # Create a temporary file path for saving the render
            temp_dir = tempfile.gettempdir()
            temp_file = os.path.join(temp_dir, "temp_render.png")
            
            # Set render to save to the temporary file
            context.scene.render.filepath = temp_file
            context.scene.render.image_settings.file_format = 'PNG'
            
            # Render the image and save to file
            self.report({'INFO'}, f"Rendering to temporary file: {temp_file}")
            bpy.ops.render.render(write_still=True)
            
            # Check if file was created
            if not os.path.exists(temp_file):
                self.report({'ERROR'}, f"Temporary render file was not created: {temp_file}")
                return None
            
            # Load the saved image using OpenCV
            import cv2
            render_array = cv2.imread(temp_file)
            if render_array is None:
                self.report({'ERROR'}, f"Could not read temporary render file with OpenCV: {temp_file}")
                return None
                
            # Convert from BGR to RGB
            render_array = cv2.cvtColor(render_array, cv2.COLOR_BGR2RGB)
            
            self.report({'INFO'}, f"Successfully loaded render with shape {render_array.shape}")
            
            # Restore original render settings
            context.scene.render.filepath = original_filepath
            context.scene.render.image_settings.file_format = original_format
            
            # Try to remove temp file
            try:
                os.remove(temp_file)
            except Exception as e:
                self.report({'WARNING'}, f"Could not remove temporary file: {str(e)}")
                
            return render_array
            
        except Exception as e:
            import traceback
            self.report({'ERROR'}, f"Error rendering view: {str(e)}")
            traceback.print_exc()
            
            # Restore original render settings
            context.scene.render.filepath = original_filepath
            context.scene.render.image_settings.file_format = original_format
            
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
            
            # Convert to BGR for comparison (OpenCV uses BGR)
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
            
            # Render and get result from file
            self.report({'INFO'}, "Rendering current view...")
            render_array = self.render_current_view(context)
            if render_array is None:
                self.report({'ERROR'}, "Failed to get render result")
                return {'CANCELLED'}
            
            # Calculate metrics
            self.report({'INFO'}, "Comparing rendered image with original...")
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
