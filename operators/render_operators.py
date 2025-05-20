"""
Render operators for RC Metrics Add-on.
"""

import bpy
import os
import numpy as np
import tempfile
from bpy_extras.image_utils import load_image

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
    
    def setup_scene_for_rendering(self, context, render_selected_only=False, selection_type='MESH', selected_mesh=None, selected_collection=None):
        """Setup the scene for rendering, optionally hiding other objects"""
        # Store original visibility states
        original_visibilities = {}
        for obj in context.scene.objects:
            # Only process mesh objects
            if obj.type == 'MESH':
                original_visibilities[obj.name] = obj.hide_render
        
        # If we're only rendering the selected mesh/collection, hide everything else
        if render_selected_only:
            if selection_type == 'MESH' and selected_mesh:
                self.report({'INFO'}, f"Rendering only selected mesh: {selected_mesh}")
                for obj in context.scene.objects:
                    if obj.type == 'MESH':
                        if obj.name == selected_mesh:
                            obj.hide_render = False  # Show the selected mesh
                        else:
                            obj.hide_render = True   # Hide other meshes
            
            elif selection_type == 'COLLECTION' and selected_collection:
                self.report({'INFO'}, f"Rendering only objects in collection: {selected_collection}")
                collection = bpy.data.collections.get(selected_collection)
                
                if collection:
                    # Get all objects in the collection (including nested ones)
                    collection_objects = set()
                    
                    def get_objects_from_collection(coll, obj_set):
                        # Add direct objects
                        for obj in coll.objects:
                            if obj.type == 'MESH':
                                obj_set.add(obj.name)
                        
                        # Add objects from child collections
                        for child_coll in coll.children:
                            get_objects_from_collection(child_coll, obj_set)
                    
                    get_objects_from_collection(collection, collection_objects)
                    
                    # Show/hide objects based on collection membership
                    for obj in context.scene.objects:
                        if obj.type == 'MESH':
                            if obj.name in collection_objects:
                                obj.hide_render = False  # Show collection objects
                            else:
                                obj.hide_render = True   # Hide other objects
        
        return original_visibilities

    def restore_scene_after_rendering(self, context, original_visibilities):
        """Restore the original visibility states of objects"""
        for obj_name, hide_state in original_visibilities.items():
            obj = context.scene.objects.get(obj_name)
            if obj:
                obj.hide_render = hide_state
    
    def render_current_view(self, context):
        """Render the current view and return the render result"""
        try:
            # Store original render settings
            original_filepath = context.scene.render.filepath
            original_format = context.scene.render.image_settings.file_format
            original_color_mode = context.scene.render.image_settings.color_mode
            
            # Create a temporary file path for saving the render with a unique timestamp
            import time
            temp_dir = tempfile.gettempdir()
            timestamp = int(time.time())
            temp_file = os.path.join(temp_dir, f"temp_render_{timestamp}.png")
            
            # Set render to save to the temporary file with RGBA
            context.scene.render.filepath = temp_file
            context.scene.render.image_settings.file_format = 'PNG'
            context.scene.render.image_settings.color_mode = 'RGBA'  # Include alpha channel
            
            # Render the image and save to file
            self.report({'INFO'}, f"Rendering to temporary file: {temp_file}")
            bpy.ops.render.render(write_still=True)
            
            # Check if file was created
            if not os.path.exists(temp_file):
                self.report({'ERROR'}, f"Temporary render file was not created: {temp_file}")
                return None, None
            
            # Load the saved image using OpenCV to get the RGBA data
            import cv2
            render_array = cv2.imread(temp_file, cv2.IMREAD_UNCHANGED)  # Load with alpha channel
            if render_array is None:
                self.report({'ERROR'}, f"Could not read temporary render file with OpenCV: {temp_file}")
                return None, None
                
            # Convert from BGRA to RGBA if needed
            if render_array.shape[2] == 4:  # Check if we have alpha channel
                # OpenCV uses BGRA, convert to RGBA
                b, g, r, a = cv2.split(render_array)
                render_array = cv2.merge([r, g, b, a])
            else:
                # No alpha channel, just convert BGR to RGB
                render_array = cv2.cvtColor(render_array, cv2.COLOR_BGR2RGB)
            
            self.report({'INFO'}, f"Successfully loaded render with shape {render_array.shape}")
            
            # Also load the render result into Blender's image system for later use
            # Check if image already exists and replace it
            render_img = bpy.data.images.get("RC_Current_Render")
            if render_img:
                # Image exists, so replace its data
                render_img.filepath = temp_file
                render_img.reload()
                self.report({'INFO'}, "Updated existing RC_Current_Render image")
            else:
                # Create new image
                render_img = bpy.data.images.load(temp_file, check_existing=False)
                render_img.name = "RC_Current_Render"
                self.report({'INFO'}, "Created new RC_Current_Render image")
            
            # Restore original render settings
            context.scene.render.filepath = original_filepath
            context.scene.render.image_settings.file_format = original_format
            context.scene.render.image_settings.color_mode = original_color_mode
            
            # We'll keep the temp file for now so we can use it later
            # It will be cleaned up when Blender closes
                
            return render_array, render_img
            
        except Exception as e:
            import traceback
            self.report({'ERROR'}, f"Error rendering view: {str(e)}")
            traceback.print_exc()
            
            # Restore original render settings
            context.scene.render.filepath = original_filepath
            context.scene.render.image_settings.file_format = original_format
            
            return None, None
    
    def create_diff_image(self, render_array, original_img, context):
        """Create a difference image between rendered and original images"""
        try:
            import cv2
            
            # Get the visualization preferences
            rc_metrics = context.scene.rc_metrics
            diff_mode = rc_metrics.diff_view_mode
            diff_multiplier = rc_metrics.diff_multiplier
            
            # Create a difference image (absolute difference)
            if render_array.shape[2] == 4:  # With alpha channel
                # Create mask from alpha channel (1 for solid pixels, 0 for transparent)
                alpha_mask = render_array[:,:,3] > 0
                
                # Initialize diff image with zeros (black transparent)
                diff_img = np.zeros_like(render_array)
                
                # Calculate absolute difference only for non-transparent pixels
                for c in range(3):  # RGB channels
                    diff_channel = np.abs(render_array[:,:,c].astype(np.int16) - 
                                        original_img[:,:,c].astype(np.int16))
                    # Only assign diff values to non-transparent pixels
                    diff_img[:,:,c] = np.where(alpha_mask, diff_channel, 0)
                
                # Set alpha channel (1 where mask is true)
                diff_img[:,:,3] = np.where(alpha_mask, 255, 0)
            else:
                # No alpha channel, just calculate absolute difference for all pixels
                diff_img = cv2.absdiff(render_array[:,:,:3], original_img)
                # Add alpha channel
                alpha_channel = np.ones((diff_img.shape[0], diff_img.shape[1]), dtype=np.uint8) * 255
                diff_img = cv2.merge([diff_img[:,:,0], diff_img[:,:,1], diff_img[:,:,2], alpha_channel])
            
            # Create a visualization based on the selected mode
            if diff_mode == 'HEATMAP':
                # Convert to grayscale for heatmap
                diff_gray = cv2.cvtColor(diff_img[:,:,:3], cv2.COLOR_RGB2GRAY)
                
                # Apply heatmap colormap
                diff_heatmap = cv2.applyColorMap((diff_gray * diff_multiplier).clip(0, 255).astype(np.uint8), 
                                                cv2.COLORMAP_JET)
                
                # Create RGBA heatmap
                alpha_mask = diff_img[:,:,3] > 0
                heatmap_rgba = np.zeros_like(diff_img)
                for c in range(3):
                    heatmap_rgba[:,:,c] = np.where(alpha_mask, diff_heatmap[:,:,c], 0)
                heatmap_rgba[:,:,3] = diff_img[:,:,3]  # Keep original alpha
                
                diff_img = heatmap_rgba
            
            elif diff_mode == 'GRAYSCALE':
                # Convert to grayscale, keep alpha
                diff_gray = cv2.cvtColor(diff_img[:,:,:3], cv2.COLOR_RGB2GRAY)
                
                # Enhance contrast
                diff_gray = (diff_gray * diff_multiplier).clip(0, 255).astype(np.uint8)
                
                # Create RGBA grayscale
                alpha_mask = diff_img[:,:,3] > 0
                gray_rgba = np.zeros_like(diff_img)
                for c in range(3):
                    gray_rgba[:,:,c] = np.where(alpha_mask, diff_gray, 0)
                gray_rgba[:,:,3] = diff_img[:,:,3]  # Keep original alpha
                
                diff_img = gray_rgba
            
            else:  # COLORIZED
                # Increase brightness of difference for better visibility
                diff_img[:,:,:3] = np.clip(diff_img[:,:,:3] * diff_multiplier, 0, 255).astype(np.uint8)
            
            # Save difference image to a temporary file with a unique timestamp
            import time
            temp_dir = tempfile.gettempdir()
            timestamp = int(time.time())
            diff_file = os.path.join(temp_dir, f"rc_diff_image_{timestamp}.png")
            
            # Save the difference image (with proper channel order for OpenCV)
            r, g, b, a = cv2.split(diff_img)
            diff_bgra = cv2.merge([b, g, r, a])
            cv2.imwrite(diff_file, diff_bgra)
            
            # Load the difference image into Blender
            # Check if difference image already exists and replace it
            diff_blender_img = bpy.data.images.get("RC_Difference")
            if diff_blender_img:
                # Image exists, so replace its data
                diff_blender_img.filepath = diff_file
                diff_blender_img.reload()
                self.report({'INFO'}, "Updated existing RC_Difference image")
            else:
                # Create new image
                diff_blender_img = bpy.data.images.load(diff_file, check_existing=False)
                diff_blender_img.name = "RC_Difference"
                self.report({'INFO'}, "Created new RC_Difference image")
            
            # Open an image editor and display the difference image
            self.show_image_in_editor(context, diff_blender_img)
            
            return diff_blender_img
        except Exception as e:
            import traceback
            self.report({'ERROR'}, f"Error creating difference image: {str(e)}")
            traceback.print_exc()
            return None
    
    def show_image_in_editor(self, context, image):
        """Open and display an image in the Image Editor"""
        # Find existing Image Editor or create a new one
        image_editor = None
        
        # First check if we already have an image editor open
        for area in context.screen.areas:
            if area.type == 'IMAGE_EDITOR':
                image_editor = area
                break
        
        # If no image editor is open, try to create one by splitting the current area
        if not image_editor and len(context.screen.areas) > 1:
            # Find an area to split (preferably not the 3D view active area)
            area_to_split = None
            for area in context.screen.areas:
                if area.type != 'VIEW_3D' or area != context.area:
                    area_to_split = area
                    break
            
            # If we found an area to split, try to split it and create an image editor
            if area_to_split and area_to_split.height > 200:  # Only split if area is large enough
                # We can't actually split the area here due to context restrictions
                # Just let the user know they need to open an Image Editor
                self.report({'INFO'}, "Open an Image Editor to view the difference image")
                return
        
        # Set the image in the editor if we have one
        if image_editor:
            image_editor.spaces.active.image = image
            self.report({'INFO'}, f"Displaying {image.name} in Image Editor")

    def calculate_metrics(self, render_array, original_image):
        """Calculate PSNR and SSIM between rendered image and original image, ignoring transparent areas"""
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
                
            # Load original image using OpenCV with alpha if possible
            original_img = cv2.imread(original_path, cv2.IMREAD_UNCHANGED)
            
            if original_img is None:
                self.report({'ERROR'}, f"Failed to load original image: {original_path}")
                return None, None
                
            # Log image dimensions
            self.report({'INFO'}, f"Original image shape: {original_img.shape}")
            self.report({'INFO'}, f"Rendered image shape: {render_array.shape}")
            
            # Resize original image if dimensions don't match
            if original_img.shape[:2] != render_array.shape[:2]:
                self.report({'INFO'}, f"Resizing original image from {original_img.shape[:2]} to {render_array.shape[:2]}")
                if original_img.shape[2] == 4:  # With alpha
                    original_img = cv2.resize(original_img, (render_array.shape[1], render_array.shape[0]), 
                                            interpolation=cv2.INTER_AREA)
                else:  # No alpha
                    original_img = cv2.resize(original_img, (render_array.shape[1], render_array.shape[0]), 
                                            interpolation=cv2.INTER_AREA)
                    # If original doesn't have alpha but render does, add an alpha channel
                    if render_array.shape[2] == 4 and original_img.shape[2] == 3:
                        alpha_channel = np.ones((original_img.shape[0], original_img.shape[1]), dtype=np.uint8) * 255
                        original_img = cv2.merge([original_img[:,:,0], original_img[:,:,1], 
                                                 original_img[:,:,2], alpha_channel])
            
            # Create a mask for non-transparent pixels (if alpha channel exists)
            mask = None
            if render_array.shape[2] == 4:
                # Create mask where alpha > 0 (non-transparent pixels)
                mask = render_array[:,:,3] > 0
                
                # Convert to BGR(A) for comparison (OpenCV uses BGR)
                render_comp = render_array[:,:,:3]  # Just use RGB channels for comparison
                original_comp = original_img[:,:,:3] if original_img.shape[2] >= 3 else original_img
            else:
                # No alpha channel, use all pixels
                render_comp = render_array
                original_comp = original_img[:,:,:3] if original_img.shape[2] >= 3 else original_img
            
            # Convert to grayscale for SSIM calculation
            original_gray = cv2.cvtColor(original_comp, cv2.COLOR_BGR2GRAY) if len(original_comp.shape) == 3 else original_comp
            rendered_gray = cv2.cvtColor(render_comp, cv2.COLOR_RGB2GRAY) if len(render_comp.shape) == 3 else render_comp
            
            # Calculate metrics with mask if available
            if mask is not None:
                # Count non-transparent pixels
                valid_pixel_count = np.count_nonzero(mask)
                if valid_pixel_count == 0:
                    self.report({'WARNING'}, "No valid (non-transparent) pixels to compare")
                    return 0, 0
                
                # Calculate PSNR only on non-transparent pixels
                # For PSNR, mask the images first
                render_masked = np.zeros_like(render_comp)
                original_masked = np.zeros_like(original_comp)
                
                for c in range(render_comp.shape[2] if len(render_comp.shape) == 3 else 1):
                    render_masked[:,:,c] = np.where(mask, render_comp[:,:,c], 0)
                    original_masked[:,:,c] = np.where(mask, original_comp[:,:,c], 0)
                
                # MSE calculation manually on masked area
                squared_diff = np.sum((render_masked.astype(np.float32) - original_masked.astype(np.float32))**2)
                mse = squared_diff / valid_pixel_count / render_comp.shape[2] if len(render_comp.shape) == 3 else 1
                psnr_value = 10 * np.log10((255**2) / mse) if mse > 0 else 100  # 100 is used when MSE is 0 (perfect match)
                
                # For SSIM, use the scikit-image function with the mask
                rendered_gray_masked = np.where(mask, rendered_gray, 0)
                original_gray_masked = np.where(mask, original_gray, 0)
                ssim_value = ssim(rendered_gray_masked, original_gray_masked, 
                                data_range=255, gaussian_weights=True, 
                                use_sample_covariance=False)
            else:
                # Calculate metrics on the whole image
                psnr_value = psnr(original_comp, render_comp)
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
            
            # Check if we have a selected mesh
            rc_metrics = context.scene.rc_metrics
            selected_mesh = rc_metrics.selected_mesh
            if not selected_mesh or selected_mesh == 'None':
                self.report({'ERROR'}, "No mesh selected. Please select a mesh first!")
                return {'CANCELLED'}
            
            # Setup scene for rendering (hide/show objects as needed)
            original_visibilities = self.setup_scene_for_rendering(
                context, 
                rc_metrics.render_selected_mesh_only, 
                selected_mesh
            )
            
            # Render and get result from file
            self.report({'INFO'}, "Rendering current view...")
            render_array, render_img = self.render_current_view(context)
            
            # Restore original visibility settings
            self.restore_scene_after_rendering(context, original_visibilities)
            
            if render_array is None:
                self.report({'ERROR'}, "Failed to get render result")
                return {'CANCELLED'}
            
            # Load original image with OpenCV for processing
            import cv2
            original_path = bpy.path.abspath(bg_image.filepath)
            original_img = cv2.imread(original_path, cv2.IMREAD_UNCHANGED)
            
            if original_img is None:
                self.report({'ERROR'}, f"Failed to load original image: {original_path}")
                return {'CANCELLED'}
                
            # Resize original image if dimensions don't match
            if original_img.shape[:2] != render_array.shape[:2]:
                original_img = cv2.resize(original_img, (render_array.shape[1], render_array.shape[0]))
            
            # Create and display the difference image
            self.report({'INFO'}, "Creating difference image...")
            diff_img = self.create_diff_image(render_array, original_img, context)
            
            # Calculate metrics
            self.report({'INFO'}, "Comparing rendered image with original...")
            psnr_value, ssim_value = self.calculate_metrics(render_array, bg_image)
            
            if psnr_value is not None and ssim_value is not None:
                # Store results in scene properties
                context.scene.rc_metrics.last_psnr = psnr_value
                context.scene.rc_metrics.last_ssim = ssim_value
                
                # Report success
                self.report({'INFO'}, f"Image comparison complete - PSNR: {psnr_value:.2f}dB, SSIM: {ssim_value:.4f}")
                
                # Inform user about the difference image
                self.report({'INFO'}, "Difference image created. Open an Image Editor to view it.")
                return {'FINISHED'}
            else:
                self.report({'ERROR'}, "Failed to calculate image metrics")
                return {'CANCELLED'}
                
        except Exception as e:
            import traceback
            self.report({'ERROR'}, f"Unexpected error: {str(e)}")
            traceback.print_exc()
            return {'CANCELLED'}

class RCMETRICS_OT_ViewRender(bpy.types.Operator):
    """View the last rendered image in the Image Editor"""
    bl_idname = "rcmetrics.view_render"
    bl_label = "View Render"
    
    def execute(self, context):
        # Check if we have a render result
        render_img = bpy.data.images.get("RC_Current_Render")
        if not render_img:
            self.report({'ERROR'}, "No render available. Please render first.")
            return {'CANCELLED'}
        
        # Make sure the image data is up-to-date
        if render_img.filepath:
            try:
                render_img.reload()
            except:
                self.report({'WARNING'}, "Could not reload the render image.")
        
        # Find or create an image editor
        image_editor = None
        for area in context.screen.areas:
            if area.type == 'IMAGE_EDITOR':
                image_editor = area
                break
        
        if not image_editor:
            self.report({'INFO'}, "Please open an Image Editor to view the render.")
        else:
            # Set the image in the editor
            image_editor.spaces.active.image = render_img
            self.report({'INFO'}, "Displaying render in Image Editor")
        
        return {'FINISHED'}

class RCMETRICS_OT_ViewDiff(bpy.types.Operator):
    """View the difference image in the Image Editor"""
    bl_idname = "rcmetrics.view_diff"
    bl_label = "View Difference"
    
    def execute(self, context):
        # Check if we have a difference image
        diff_img = bpy.data.images.get("RC_Difference")
        if not diff_img:
            self.report({'ERROR'}, "No difference image available. Please render first.")
            return {'CANCELLED'}
        
        # Make sure the image data is up-to-date
        if diff_img.filepath:
            try:
                diff_img.reload()
            except:
                self.report({'WARNING'}, "Could not reload the difference image.")
        
        # Find or create an image editor
        image_editor = None
        for area in context.screen.areas:
            if area.type == 'IMAGE_EDITOR':
                image_editor = area
                break
        
        if not image_editor:
            self.report({'INFO'}, "Please open an Image Editor to view the difference image.")
        else:
            # Set the image in the editor
            image_editor.spaces.active.image = diff_img
            self.report({'INFO'}, "Displaying difference image in Image Editor")
        
        return {'FINISHED'}

# Registration
def register():
    bpy.utils.register_class(RCMETRICS_OT_RenderCompare)
    bpy.utils.register_class(RCMETRICS_OT_ViewRender)
    bpy.utils.register_class(RCMETRICS_OT_ViewDiff)

def unregister():
    bpy.utils.unregister_class(RCMETRICS_OT_ViewDiff)
    bpy.utils.unregister_class(RCMETRICS_OT_ViewRender)
    bpy.utils.unregister_class(RCMETRICS_OT_RenderCompare)
