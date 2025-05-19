"""
Manual rendering operators for RC Metrics Add-on.
This module provides a manual workflow for rendering and calculating metrics.
"""

import bpy
import os
from bpy.props import StringProperty, BoolProperty

class RCMETRICS_OT_PrepareManualRender(bpy.types.Operator):
    """Prepare for manual rendering and set up the selected camera"""
    bl_idname = "rcmetrics.prepare_manual_render"
    bl_label = "2. Prepare for Manual Rendering"
    bl_options = {'REGISTER', 'UNDO'}
    
    switch_to_render_workspace: BoolProperty(
        name="Switch to Render Workspace",
        description="Switch to Rendering workspace automatically",
        default=True
    )
    
    def execute(self, context):
        from ..utils import camera_utils
        from ..utils import render_utils
        
        # Check active object
        if not context.active_object or context.active_object.type != 'MESH':
            self.report({'ERROR'}, "Please select a mesh object to evaluate")
            return {'CANCELLED'}
        
        # Get enabled camera
        rc_metrics = context.scene.rc_metrics
        enabled_cameras = camera_utils.get_enabled_cameras(context)
        
        if not enabled_cameras:
            # No camera selected, try to select the active one
            active_index = rc_metrics.active_camera_index
            if 0 <= active_index < len(rc_metrics.cameras):
                camera_name = camera_utils.select_single_camera(context, active_index)
                if camera_name:
                    self.report({'INFO'}, f"Auto-selected camera: {camera_name}")
                    # Re-check if we have the camera now
                    enabled_cameras = camera_utils.get_enabled_cameras(context)
        
        if not enabled_cameras:
            self.report({'ERROR'}, "No camera selected. Please select a camera first.")
            return {'CANCELLED'}
        
        # Get the first enabled camera
        camera = enabled_cameras[0]
        
        # Setup render settings
        render_utils.setup_render_settings(context, rc_metrics.render_quality)
        
        # Set the active camera
        scene = context.scene
        scene.camera = camera
        
        # Set up an image editor to view the render result directly
        if self.switch_to_render_workspace:
            # Try to switch to the "Rendering" workspace if it exists
            for workspace in bpy.data.workspaces:
                if workspace.name == "Rendering":
                    context.window.workspace = workspace
                    self.report({'INFO'}, "Switched to Rendering workspace")
                    break
        
        # Set output path if saving renders
        if rc_metrics.save_renders:
            if not rc_metrics.metrics_output:
                # Create a default output folder if not specified
                rc_metrics.metrics_output = os.path.join(rc_metrics.rc_folder, "metrics_output")
                try:
                    os.makedirs(rc_metrics.metrics_output, exist_ok=True)
                except:
                    self.report({'ERROR'}, f"Could not create output directory: {rc_metrics.metrics_output}")
                    return {'CANCELLED'}
            
            # Create render output directory
            render_output = os.path.join(rc_metrics.metrics_output, "renders")
            try:
                os.makedirs(render_output, exist_ok=True)
            except:
                self.report({'ERROR'}, f"Could not create render output directory: {render_output}")
                return {'CANCELLED'}
                
            # Set render output path
            scene.render.filepath = os.path.join(render_output, f"{camera.name.split('.')[0]}_render.png")
        
        # Show info message
        self.report({'INFO'}, f"Ready to render with camera: {camera.name}")
        self.report({'INFO'}, "Press F12 to render, then use 'Calculate Metrics from Current Render'")
        
        return {'FINISHED'}

class RCMETRICS_OT_CalculateMetricsFromRender(bpy.types.Operator):
    """Calculate metrics using the current render result"""
    bl_idname = "rcmetrics.calculate_metrics_from_render"
    bl_label = "3. Calculate Metrics from Current Render"
    bl_options = {'REGISTER', 'UNDO'}
    
    def get_render_result_image(self, context):
        """Get the render result from viewer node or render result area"""
        # First try to get from render result datablock
        if bpy.data.images.get('Render Result'):
            return bpy.data.images['Render Result']
        
        # If not found, try to get from compositor viewer node
        if context.scene.use_nodes and context.scene.node_tree:
            for node in context.scene.node_tree.nodes:
                if node.type == 'VIEWER':
                    if node.image:
                        return node.image
        
        # If still not found, check for render result in image editor areas
        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'IMAGE_EDITOR':
                    if area.spaces.active.image and area.spaces.active.image.name == 'Render Result':
                        return area.spaces.active.image
        
        return None
    
    def execute(self, context):
        from ..utils import camera_utils
        from ..utils import render_utils
        from ..utils import image_utils
        
        rc_metrics = context.scene.rc_metrics
        
        # Get render result from various possible sources
        render_img = self.get_render_result_image(context)
        
        if not render_img:
            self.report({'ERROR'}, "No render result found. Please render first (F12).")
            return {'CANCELLED'}
        
        # Get the active camera
        if not context.scene.camera:
            self.report({'ERROR'}, "No active camera. Please run 'Prepare for Manual Rendering' first.")
            return {'CANCELLED'}
        
        camera = context.scene.camera
        
        # Get reference image
        self.report({'INFO'}, f"Getting reference image for camera: {camera.name}")
        ref_img = render_utils.get_camera_background_image(camera)
        
        if ref_img is None:
            self.report({'ERROR'}, f"Failed to get reference image for camera: {camera.name}")
            return {'CANCELLED'}
        
        # Check render image size
        width, height = render_img.size
        
        if width == 0 or height == 0:
            self.report({'ERROR'}, "Invalid render size.")
            return {'CANCELLED'}
        
        # Convert render to numpy array
        try:
            import numpy as np
            
            # Get pixels array
            pixels = np.array(render_img.pixels[:])
            
            # Check if we have enough pixels
            expected_pixels = width * height * 4  # RGBA format
            if len(pixels) < expected_pixels:
                self.report({'ERROR'}, f"Not enough pixels in render result. Expected {expected_pixels}, got {len(pixels)}")
                return {'CANCELLED'}
            
            # Reshape and convert
            render_array = pixels.reshape((height, width, 4))
            # Convert from RGBA to BGR (OpenCV format)
            render_array = render_array[:, :, :3][:, :, ::-1]
            # Convert from float [0,1] to uint8 [0,255]
            rendered_img = (render_array * 255).astype(np.uint8)
            
            self.report({'INFO'}, f"Converted render to array, shape: {rendered_img.shape}")
            
        except Exception as e:
            self.report({'ERROR'}, f"Error converting render: {e}")
            return {'CANCELLED'}
        
        # Ensure rendered image and reference image have the same dimensions
        if rendered_img.shape != ref_img.shape:
            try:
                import cv2
                self.report({'INFO'}, f"Resizing rendered image from {rendered_img.shape} to {ref_img.shape}")
                rendered_img = cv2.resize(rendered_img, (ref_img.shape[1], ref_img.shape[0]))
            except Exception as e:
                self.report({'ERROR'}, f"Error resizing image: {e}")
                return {'CANCELLED'}
        
        # Calculate metrics
        self.report({'INFO'}, "Calculating metrics...")
        psnr, ssim = image_utils.calculate_image_metrics(ref_img, rendered_img)
        
        if psnr is None or ssim is None:
            self.report({'ERROR'}, "Failed to calculate metrics.")
            return {'CANCELLED'}
        
        # Update metrics in the UI
        result = camera_utils.update_camera_results(
            context, camera.name, psnr, ssim,
            rc_metrics.psnr_threshold, rc_metrics.ssim_threshold)
        
        if not result:
            self.report({'WARNING'}, f"Failed to update UI for camera: {camera.name}")
        
        # Create or update metrics summary
        metrics_summary = {
            "mesh_name": context.active_object.name if context.active_object else "Unknown",
            "cameras": [{
                "camera": camera.name,
                "psnr": psnr,
                "ssim": ssim
            }],
            "average_psnr": psnr,
            "average_ssim": ssim,
            "min_psnr": psnr,
            "min_ssim": ssim,
            "max_psnr": psnr,
            "max_ssim": ssim
        }
        
        # Update averages in the UI
        rc_metrics.average_psnr = psnr
        rc_metrics.average_ssim = ssim
        rc_metrics.has_results = True
        
        # Save metrics to file if we're saving renders
        if rc_metrics.save_renders and rc_metrics.metrics_output:
            import json
            metrics_file = os.path.join(rc_metrics.metrics_output, 
                                      f"metrics_manual_{metrics_summary['mesh_name']}.json")
            try:
                with open(metrics_file, 'w') as f:
                    json.dump(metrics_summary, f, indent=4)
                self.report({'INFO'}, f"Metrics saved to: {metrics_file}")
            except Exception as e:
                self.report({'WARNING'}, f"Failed to save metrics: {e}")
        
        # Report results
        self.report({'INFO'}, f"Results for {camera.name}: PSNR={psnr:.2f}, SSIM={ssim:.4f}")
        
        # Force UI update
        for area in context.screen.areas:
            area.tag_redraw()
        
        return {'FINISHED'}

class RCMETRICS_OT_ViewSideBySide(bpy.types.Operator):
    """Open a side-by-side view of the render result and original image"""
    bl_idname = "rcmetrics.view_side_by_side"
    bl_label = "View Side by Side"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Find or create image editor areas
        image_editors = []
        
        # First, try to find existing image editors
        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'IMAGE_EDITOR':
                    image_editors.append(area)
        
        # If we don't have at least two image editors, try to split an existing one
        if len(image_editors) < 2:
            # Try a simpler approach for Blender 4.2+
            try:
                # Split the 3D View area into two image editors
                for window in context.window_manager.windows:
                    for area in window.screen.areas:
                        if area.type == 'VIEW_3D':
                            # Convert the 3D View to an image editor
                            area.type = 'IMAGE_EDITOR'
                            image_editors.append(area)
                            
                            # Now create a new area by splitting
                            if area.width > area.height:
                                dir = 'VERTICAL'
                            else:
                                dir = 'HORIZONTAL'
                                
                            # Using the newer method in Blender 4.2+
                            with context.temp_override(area=area):
                                bpy.ops.screen.area_split(direction=dir, factor=0.5)
                            
                            # Find the newly created area
                            for new_area in window.screen.areas:
                                if new_area not in image_editors and new_area.type == 'VIEW_3D':
                                    new_area.type = 'IMAGE_EDITOR'
                                    image_editors.append(new_area)
                                    break
                            
                            if len(image_editors) >= 2:
                                break
                    
                    if len(image_editors) >= 2:
                        break
            except Exception as e:
                self.report({'WARNING'}, f"Error setting up view: {e}")
        
        # If we still don't have enough image editor areas, notify the user
        if len(image_editors) < 2:
            self.report({'ERROR'}, "Could not create enough image editor areas")
            return {'CANCELLED'}
        
        # Get the camera
        camera = context.scene.camera
        if not camera:
            self.report({'ERROR'}, "No active camera")
            return {'CANCELLED'}
        
        # Get the render result
        render_result = None
        for img in bpy.data.images:
            if img.name == 'Render Result':
                render_result = img
                break
        
        if not render_result:
            self.report({'ERROR'}, "No render result available")
            return {'CANCELLED'}
        
        # Find the background image for the camera
        bg_image = None
        if camera.data.background_images and camera.data.background_images[0].image:
            bg_image = camera.data.background_images[0].image
        
        if not bg_image:
            self.report({'ERROR'}, "No background image for camera")
            return {'CANCELLED'}
        
        # Set images in image editors
        try:
            # Set the first editor to show the render result
            image_editors[0].spaces.active.image = render_result
            
            # Set the second editor to show the background image
            image_editors[1].spaces.active.image = bg_image
            
            self.report({'INFO'}, "Set up side-by-side view")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error setting up side-by-side view: {e}")
            return {'CANCELLED'}

# Registration
def register():
    bpy.utils.register_class(RCMETRICS_OT_PrepareManualRender)
    bpy.utils.register_class(RCMETRICS_OT_CalculateMetricsFromRender)
    bpy.utils.register_class(RCMETRICS_OT_ViewSideBySide)

def unregister():
    bpy.utils.unregister_class(RCMETRICS_OT_ViewSideBySide)
    bpy.utils.unregister_class(RCMETRICS_OT_CalculateMetricsFromRender)
    bpy.utils.unregister_class(RCMETRICS_OT_PrepareManualRender)
