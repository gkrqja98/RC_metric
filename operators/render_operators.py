"""
Render operators for RC Metrics Add-on.
"""

import bpy
import os
import numpy as np
import tempfile
from bpy_extras.image_utils import load_image

class RCMETRICS_OT_Render(bpy.types.Operator):
    """Render the current camera view"""
    bl_idname = "rcmetrics.render"
    bl_label = "Render View"
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
            original_film_transparent = context.scene.render.film_transparent  # 투명 설정 저장
            
            # 투명 배경 설정 활성화
            context.scene.render.film_transparent = True
            
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
            self.report({'INFO'}, "Transparent background enabled for rendering")
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
            context.scene.render.film_transparent = original_film_transparent  # 투명 설정 복원
            
            # We'll keep the temp file for now so we can use it later
            # It will be cleaned up when Blender closes
                
            return render_array, render_img
            
        except Exception as e:
            import traceback
            self.report({'ERROR'}, f"Error rendering view: {str(e)}")
            traceback.print_exc()
            
            # Restore original render settings if they were set
            try:
                context.scene.render.filepath = original_filepath
                context.scene.render.image_settings.file_format = original_format
                context.scene.render.image_settings.color_mode = original_color_mode
                context.scene.render.film_transparent = original_film_transparent  # 오류 발생해도 투명 설정 복원
            except:
                pass
            
            return None, None
    
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
                self.report({'INFO'}, "Open an Image Editor to view the rendered image")
                return
        
        # Set the image in the editor if we have one
        if image_editor:
            image_editor.spaces.active.image = image
            self.report({'INFO'}, f"Displaying {image.name} in Image Editor")
    
    def execute(self, context):
        try:
            # Check if we have active camera with background image
            camera_ok, bg_image = self.check_active_camera(context)
            if not camera_ok:
                return {'CANCELLED'}
            
            # Check if we have a selected mesh or collection
            rc_metrics = context.scene.rc_metrics
            selection_type = rc_metrics.selection_type
            selected_mesh = None
            selected_collection = None
            
            if selection_type == 'MESH':
                selected_mesh = rc_metrics.selected_mesh
                if not selected_mesh or selected_mesh == 'None':
                    self.report({'ERROR'}, "No mesh selected. Please select a mesh first!")
                    return {'CANCELLED'}
            else:  # COLLECTION
                selected_collection = rc_metrics.selected_collection
                if not selected_collection or selected_collection == 'None':
                    self.report({'ERROR'}, "No collection selected. Please select a collection first!")
                    return {'CANCELLED'}
            
            # Setup scene for rendering (hide/show objects as needed)
            original_visibilities = self.setup_scene_for_rendering(
                context, 
                rc_metrics.render_selected_only,
                selection_type,
                selected_mesh,
                selected_collection
            )
            
            # Render and get result from file
            self.report({'INFO'}, "Rendering current view...")
            render_array, render_img = self.render_current_view(context)
            
            # Restore original visibility settings
            self.restore_scene_after_rendering(context, original_visibilities)
            
            if render_array is None:
                self.report({'ERROR'}, "Failed to get render result")
                return {'CANCELLED'}
            
            # Show rendered image in the Image Editor
            self.show_image_in_editor(context, render_img)
            
            # Report success
            self.report({'INFO'}, "Rendering completed successfully")
            return {'FINISHED'}
                
        except Exception as e:
            import traceback
            self.report({'ERROR'}, f"Unexpected error: {str(e)}")
            traceback.print_exc()
            return {'CANCELLED'}

class RCMETRICS_OT_Compare(bpy.types.Operator):
    """Compare rendered image with original image using different modes"""
    bl_idname = "rcmetrics.compare"
    bl_label = "Compare Images"
    bl_options = {'REGISTER', 'UNDO'}
    
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
    
    def ssim_color(self, img1, img2):
        from skimage.metrics import structural_similarity as ssim
        ssim_r = ssim(img1[:,:,0], img2[:,:,0], data_range=255)
        ssim_g = ssim(img1[:,:,1], img2[:,:,1], data_range=255)
        ssim_b = ssim(img1[:,:,2], img2[:,:,2], data_range=255)
        return (ssim_r + ssim_g + ssim_b) / 3

    def ssim_weighted(self, img1, img2, weights):
        from skimage.metrics import structural_similarity as ssim
        ssim_r = ssim(img1[:,:,0], img2[:,:,0], data_range=255)
        ssim_g = ssim(img1[:,:,1], img2[:,:,1], data_range=255)
        ssim_b = ssim(img1[:,:,2], img2[:,:,2], data_range=255)
        return ssim_r * weights[0] + ssim_g * weights[1] + ssim_b * weights[2]

    def calculate_metrics_standard(self, render_array, original_img):
        """Standard metrics calculation on entire image"""
        try:
            # Import necessary modules
            import cv2
            from skimage.metrics import structural_similarity as ssim
            from skimage.metrics import peak_signal_noise_ratio as psnr
            
            # Convert to the same format for comparison
            render_comp = render_array[:,:,:3] if render_array.shape[2] >= 3 else render_array
            original_comp = original_img[:,:,:3] if original_img.shape[2] >= 3 else original_img
            
            # SSIM mode 분기
            scene = bpy.context.scene
            rc_metrics = scene.rc_metrics if hasattr(scene, 'rc_metrics') else None
            ssim_mode = rc_metrics.ssim_mode if rc_metrics else 'GRAY'
            ssim_weights = rc_metrics.ssim_weights if rc_metrics else (0.333, 0.333, 0.334)
            
            # Calculate metrics on the whole image
            psnr_value = psnr(original_comp, render_comp)
            
            if ssim_mode == 'GRAY':
                # Convert to grayscale for SSIM calculation
                original_gray = cv2.cvtColor(original_comp, cv2.COLOR_BGR2GRAY) if len(original_comp.shape) == 3 else original_comp
                rendered_gray = cv2.cvtColor(render_comp, cv2.COLOR_RGB2GRAY) if len(render_comp.shape) == 3 else render_comp
                ssim_value = ssim(original_gray, rendered_gray, data_range=255, gaussian_weights=True, use_sample_covariance=False)
            elif ssim_mode == 'COLOR':
                ssim_value = self.ssim_color(original_comp, render_comp)
            elif ssim_mode == 'WEIGHTED':
                ssim_value = self.ssim_weighted(original_comp, render_comp, ssim_weights)
            else:
                # fallback
                original_gray = cv2.cvtColor(original_comp, cv2.COLOR_BGR2GRAY) if len(original_comp.shape) == 3 else original_comp
                rendered_gray = cv2.cvtColor(render_comp, cv2.COLOR_RGB2GRAY) if len(render_comp.shape) == 3 else render_comp
                ssim_value = ssim(original_gray, rendered_gray, data_range=255, gaussian_weights=True, use_sample_covariance=False)
            
            self.report({'INFO'}, f"Standard metrics - PSNR: {psnr_value:.2f}dB, SSIM: {ssim_value:.4f} (mode: {ssim_mode})")
            
            return psnr_value, ssim_value
            
        except Exception as e:
            import traceback
            self.report({'ERROR'}, f"Error calculating standard metrics: {str(e)}")
            traceback.print_exc()
            return None, None
    
    def calculate_metrics_no_transparent(self, render_array, original_img, context):
        """Calculate metrics excluding transparent areas"""
        try:
            # Import necessary modules
            import cv2
            import numpy as np
            from skimage.metrics import structural_similarity as ssim
            
            rc_metrics = context.scene.rc_metrics if hasattr(context.scene, 'rc_metrics') else None
            ssim_mode = rc_metrics.ssim_mode if rc_metrics else 'GRAY'
            ssim_weights = rc_metrics.ssim_weights if rc_metrics else (0.333, 0.333, 0.334)
            
            # Create mask for non-transparent pixels
            if render_array.shape[2] == 4:
                # 알파 채널을 분리합니다.
                alpha = render_array[:,:,3]  # 첫 번째 이미지의 알파 채널
                alpha_mask = alpha > 0  # 투명하지 않은 부분만 비교하도록 마스크 생성
                
                # Print statistics about the transparency mask
                total_pixels = alpha_mask.size
                opaque_pixels = np.count_nonzero(alpha_mask)
                transparent_pixels = total_pixels - opaque_pixels
                transparent_ratio = transparent_pixels / total_pixels * 100
                
                self.report({'INFO'}, f"투명 픽셀: {transparent_pixels}/{total_pixels} ({transparent_ratio:.2f}%)")
                self.report({'INFO'}, f"불투명 픽셀: {opaque_pixels}/{total_pixels} ({100-transparent_ratio:.2f}%)")
                
                # 투명한 부분을 제외한 두 이미지를 비교합니다.
                image1_rgb = render_array[:,:,:3]  # 알파 채널을 제외한 RGB 부분만 사용
                image2_rgb = original_img[:,:,:3] if original_img.shape[2] >= 3 else original_img  # 두 번째 이미지에서 RGB만 사용
                
                # Count non-transparent pixels
                valid_pixel_count = np.count_nonzero(alpha_mask)
                if valid_pixel_count == 0:
                    self.report({'WARNING'}, "No valid (non-transparent) pixels to compare")
                    return 0, 0
                
                # 투명한 부분을 제외한 MSE 계산
                # Use the requested calculation method
                mse = np.mean((image1_rgb[alpha_mask] - image2_rgb[alpha_mask]) ** 2)
                
                # PSNR 계산
                if mse == 0:
                    psnr_value = float('inf')
                else:
                    pixel_max = 255.0
                    psnr_value = 20 * np.log10(pixel_max / np.sqrt(mse))
            else:
                # No alpha channel, use all pixels
                mask = np.ones(render_array.shape[:2], dtype=bool)
                image1_rgb = render_array
                image2_rgb = original_img[:,:,:3] if original_img.shape[2] >= 3 else original_img
                
                # Calculate MSE and PSNR for non-alpha images
                mse = np.mean((image1_rgb - image2_rgb) ** 2)
                if mse == 0:
                    psnr_value = float('inf')
                else:
                    pixel_max = 255.0
                    psnr_value = 20 * np.log10(pixel_max / np.sqrt(mse))
            
            # SSIM 계산
            if ssim_mode == 'GRAY':
                # Convert to grayscale for SSIM calculation
                original_gray = cv2.cvtColor(image2_rgb, cv2.COLOR_BGR2GRAY) if len(image2_rgb.shape) == 3 else image2_rgb
                rendered_gray = cv2.cvtColor(image1_rgb, cv2.COLOR_RGB2GRAY) if len(image1_rgb.shape) == 3 else image1_rgb
                if render_array.shape[2] == 4:
                    rendered_gray_masked = np.where(alpha_mask, rendered_gray, 0)
                    original_gray_masked = np.where(alpha_mask, original_gray, 0)
                    ssim_value = ssim(rendered_gray_masked, original_gray_masked, 
                                    data_range=255, gaussian_weights=True, 
                                    use_sample_covariance=False)
                else:
                    ssim_value = ssim(rendered_gray, original_gray, 
                                    data_range=255, gaussian_weights=True, 
                                    use_sample_covariance=False)
            elif ssim_mode == 'COLOR':
                ssim_value = self.ssim_color(image2_rgb, image1_rgb)
            elif ssim_mode == 'WEIGHTED':
                ssim_value = self.ssim_weighted(image2_rgb, image1_rgb, ssim_weights)
            else:
                original_gray = cv2.cvtColor(image2_rgb, cv2.COLOR_BGR2GRAY) if len(image2_rgb.shape) == 3 else image2_rgb
                rendered_gray = cv2.cvtColor(image1_rgb, cv2.COLOR_RGB2GRAY) if len(image1_rgb.shape) == 3 else image1_rgb
                ssim_value = ssim(rendered_gray, original_gray, data_range=255, gaussian_weights=True, use_sample_covariance=False)
            
            self.report({'INFO'}, f"No-transparent metrics - PSNR: {psnr_value:.2f}dB, SSIM: {ssim_value:.4f}")
            
            return psnr_value, ssim_value
            
        except Exception as e:
            import traceback
            self.report({'ERROR'}, f"Error calculating no-transparent metrics: {str(e)}")
            traceback.print_exc()
            return None, None
    
    def calculate_metrics_edges_only(self, render_array, original_img, edge_thickness=20):
        """Calculate metrics only on edge areas"""
        try:
            # Import necessary modules
            import cv2
            import numpy as np
            from skimage.metrics import structural_similarity as ssim
            from skimage.metrics import peak_signal_noise_ratio as psnr
            
            # Get image dimensions
            height, width = render_array.shape[:2]
            
            # Create edge mask (pixels within edge_thickness of the border)
            edge_mask = np.zeros((height, width), dtype=bool)
            
            # Set outer edge_thickness pixels to True
            edge_mask[:edge_thickness, :] = True  # Top edge
            edge_mask[-edge_thickness:, :] = True  # Bottom edge
            edge_mask[:, :edge_thickness] = True  # Left edge
            edge_mask[:, -edge_thickness:] = True  # Right edge
            
            # If we have alpha channel, combine with transparency mask
            alpha_mask = None
            if render_array.shape[2] == 4:
                # Only include edge pixels that are also non-transparent
                alpha_mask = render_array[:,:,3] > 0
                
                # Print statistics about the transparency mask
                total_pixels = alpha_mask.size
                opaque_pixels = np.count_nonzero(alpha_mask)
                transparent_pixels = total_pixels - opaque_pixels
                transparent_ratio = transparent_pixels / total_pixels * 100
                
                self.report({'INFO'}, f"투명 픽셀: {transparent_pixels}/{total_pixels} ({transparent_ratio:.2f}%)")
                self.report({'INFO'}, f"불투명 픽셀: {opaque_pixels}/{total_pixels} ({100-transparent_ratio:.2f}%)")
                
                # Combine masks - only use edge pixels that are not transparent
                combined_mask = np.logical_and(edge_mask, alpha_mask)
                
                # 만약 결합된 마스크에 유효한 픽셀이 없다면 알파 마스크만 사용
                if np.count_nonzero(combined_mask) == 0:
                    self.report({'WARNING'}, "알파와 결합된 가장자리 마스크에 유효한 픽셀이 없습니다. 전체 불투명 영역을 사용합니다.")
                    edge_mask = alpha_mask.copy()
                else:
                    edge_mask = combined_mask
            
            # Prepare images for comparison
            render_comp = render_array[:,:,:3]  # Just use RGB channels
            original_comp = original_img[:,:,:3] if original_img.shape[2] >= 3 else original_img
            
            # Convert to grayscale for SSIM
            original_gray = cv2.cvtColor(original_comp, cv2.COLOR_BGR2GRAY) if len(original_comp.shape) == 3 else original_comp
            rendered_gray = cv2.cvtColor(render_comp, cv2.COLOR_RGB2GRAY) if len(render_comp.shape) == 3 else render_comp
            
            # Count valid edge pixels
            valid_pixel_count = np.count_nonzero(edge_mask)
            if valid_pixel_count == 0:
                self.report({'WARNING'}, "No valid edge pixels to compare")
                return 0, 0
            
            # 유효한 마스크 픽셀 비율 출력
            mask_ratio = valid_pixel_count / (height * width) * 100
            self.report({'INFO'}, f"마스크 적용 픽셀 비율: {mask_ratio:.2f}% ({valid_pixel_count} / {height * width})")
            
            # Mask images for edge-only comparison
            render_masked = np.zeros_like(render_comp)
            original_masked = np.zeros_like(original_comp)
            
            for c in range(3):  # RGB channels
                render_masked[:,:,c] = np.where(edge_mask, render_comp[:,:,c], 0)
                original_masked[:,:,c] = np.where(edge_mask, original_comp[:,:,c], 0)
            
            # Calculate MSE manually for PSNR
            squared_diff = np.sum((render_masked.astype(np.float32) - original_masked.astype(np.float32))**2)
            mse = squared_diff / valid_pixel_count / 3  # Divide by valid pixels and channel count
            psnr_value = 10 * np.log10((255**2) / mse) if mse > 0 else 100
            
            # Calculate SSIM on edge areas
            rendered_gray_masked = np.where(edge_mask, rendered_gray, 0)
            original_gray_masked = np.where(edge_mask, original_gray, 0)
            ssim_value = ssim(rendered_gray_masked, original_gray_masked, 
                            data_range=255, gaussian_weights=True, 
                            use_sample_covariance=False)
            
            self.report({'INFO'}, f"Edge-only metrics - PSNR: {psnr_value:.2f}dB, SSIM: {ssim_value:.4f}")
            
            # Create visualization of edge mask for debugging
            # This helps to see which pixels were used in the comparison
            edge_vis = np.zeros((height, width, 4), dtype=np.uint8)
            edge_vis[edge_mask, 0] = 255  # Red channel for edge pixels
            edge_vis[edge_mask, 3] = 200  # Alpha for edge pixels
            
            # 가장자리 마스크 시각화 저장
            temp_dir = tempfile.gettempdir()
            import time
            timestamp = int(time.time())
            edge_file = os.path.join(temp_dir, f"rc_edge_mask_{timestamp}.png")
            cv2.imwrite(edge_file, cv2.cvtColor(edge_vis, cv2.COLOR_RGBA2BGRA))
            
            # 블렌더에 마스크 이미지 로드
            edge_img = bpy.data.images.get("RC_Edge_Mask")
            if edge_img:
                edge_img.filepath = edge_file
                edge_img.reload()
                self.report({'INFO'}, "업데이트된 가장자리 마스크 이미지")
            else:
                edge_img = bpy.data.images.load(edge_file, check_existing=False)
                edge_img.name = "RC_Edge_Mask"
                self.report({'INFO'}, "생성된 가장자리 마스크 이미지")
            
            return psnr_value, ssim_value
            
        except Exception as e:
            import traceback
            self.report({'ERROR'}, f"Error calculating edge-only metrics: {str(e)}")
            traceback.print_exc()
            return None, None
    
    def execute(self, context):
        try:
            # 렌더링된 이미지 확인
            render_img = bpy.data.images.get("RC_Current_Render")
            if not render_img:
                self.report({'ERROR'}, "No render available. Please render first.")
                return {'CANCELLED'}
            
            # 렌더링된 이미지 데이터 가져오기
            render_path = bpy.path.abspath(render_img.filepath)
            import cv2
            import numpy as np
            render_array = cv2.imread(render_path, cv2.IMREAD_UNCHANGED)
            
            if render_array is None:
                self.report({'ERROR'}, f"Failed to read render image: {render_path}")
                return {'CANCELLED'}
                
            # OpenCV는 BGRA, 우리는 RGBA가 필요
            if render_array.shape[2] == 4:
                b, g, r, a = cv2.split(render_array)
                render_array = cv2.merge([r, g, b, a])
            else:
                render_array = cv2.cvtColor(render_array, cv2.COLOR_BGR2RGB)
            
            # 활성 카메라의 배경 이미지 가져오기
            if not context.scene.camera:
                self.report({'ERROR'}, "No active camera selected.")
                return {'CANCELLED'}
                
            cam_data = context.scene.camera.data
            bg_image = None
            
            if hasattr(cam_data, 'background_images') and cam_data.background_images:
                for bg in cam_data.background_images:
                    if bg.image:
                        bg_image = bg.image
                        break
            
            if not bg_image:
                self.report({'ERROR'}, "Active camera does not have a background image.")
                return {'CANCELLED'}
            
            # 원본 이미지 로드
            original_path = bpy.path.abspath(bg_image.filepath)
            original_img = cv2.imread(original_path, cv2.IMREAD_UNCHANGED)
            
            if original_img is None:
                self.report({'ERROR'}, f"Failed to load original image: {original_path}")
                return {'CANCELLED'}
                
            # 크기가 다르면 원본 이미지 리사이즈
            if original_img.shape[:2] != render_array.shape[:2]:
                original_img = cv2.resize(original_img, (render_array.shape[1], render_array.shape[0]),
                                       interpolation=cv2.INTER_AREA)
            
            # 선택된 비교 모드에 따라 메트릭 계산
            rc_metrics = context.scene.rc_metrics
            compare_mode = rc_metrics.compare_mode
            
            if compare_mode == 'STANDARD':
                psnr_value, ssim_value = self.calculate_metrics_standard(render_array, original_img)
            elif compare_mode == 'NO_TRANSPARENT':
                psnr_value, ssim_value = self.calculate_metrics_no_transparent(render_array, original_img, context)
            elif compare_mode == 'EDGES_ONLY':
                psnr_value, ssim_value = self.calculate_metrics_edges_only(
                    render_array, original_img, rc_metrics.edge_thickness)
            
            # 결과가 유효하면 저장 및 디스플레이
            if psnr_value is not None and ssim_value is not None:
                context.scene.rc_metrics.last_psnr = psnr_value
                context.scene.rc_metrics.last_ssim = ssim_value
                
                # 차이 이미지 생성
                diff_img = self.create_diff_image(render_array, original_img, context)
                
                # 차이 이미지 표시
                if diff_img:
                    self.show_image_in_editor(context, diff_img)
                
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
            self.report({'ERROR'}, "No difference image available. Please compare first.")
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

class RCMETRICS_OT_ViewEdgeMask(bpy.types.Operator):
    """View the edge mask used for edge-only comparison"""
    bl_idname = "rcmetrics.view_edge_mask"
    bl_label = "View Edge Mask"
    
    def execute(self, context):
        # Check if we have an edge mask image
        edge_img = bpy.data.images.get("RC_Edge_Mask")
        if not edge_img:
            self.report({'ERROR'}, "No edge mask available. Please run edge comparison first.")
            return {'CANCELLED'}
        
        # Make sure the image data is up-to-date
        if edge_img.filepath:
            try:
                edge_img.reload()
            except:
                self.report({'WARNING'}, "Could not reload the edge mask image.")
        
        # Find or create an image editor
        image_editor = None
        for area in context.screen.areas:
            if area.type == 'IMAGE_EDITOR':
                image_editor = area
                break
        
        if not image_editor:
            self.report({'INFO'}, "Please open an Image Editor to view the edge mask.")
        else:
            # Set the image in the editor
            image_editor.spaces.active.image = edge_img
            self.report({'INFO'}, "Displaying edge mask in Image Editor")
        
        return {'FINISHED'}

# Legacy operator that calls both render and compare
class RCMETRICS_OT_RenderCompare(bpy.types.Operator):
    """Render the current camera view and compare with the original image (legacy)"""
    bl_idname = "rcmetrics.render_compare"
    bl_label = "Render and Compare"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # First call the render operator
        bpy.ops.rcmetrics.render()
        
        # Then call the compare operator
        bpy.ops.rcmetrics.compare()
        
        return {'FINISHED'}

# Registration
def register():
    bpy.utils.register_class(RCMETRICS_OT_Render)
    bpy.utils.register_class(RCMETRICS_OT_Compare)
    bpy.utils.register_class(RCMETRICS_OT_ViewRender)
    bpy.utils.register_class(RCMETRICS_OT_ViewDiff)
    bpy.utils.register_class(RCMETRICS_OT_ViewEdgeMask)
    bpy.utils.register_class(RCMETRICS_OT_RenderCompare)

def unregister():
    bpy.utils.unregister_class(RCMETRICS_OT_RenderCompare)
    bpy.utils.unregister_class(RCMETRICS_OT_ViewEdgeMask)
    bpy.utils.unregister_class(RCMETRICS_OT_ViewDiff)
    bpy.utils.unregister_class(RCMETRICS_OT_ViewRender)
    bpy.utils.unregister_class(RCMETRICS_OT_Compare)
    bpy.utils.unregister_class(RCMETRICS_OT_Render)
