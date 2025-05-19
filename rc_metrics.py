import bpy
import os
import json
import time
import numpy as np
from bpy.props import (StringProperty, BoolProperty, FloatProperty, 
                      EnumProperty, IntProperty, CollectionProperty, PointerProperty)
from bpy.types import PropertyGroup

from . import camera_utils
from . import render_utils
from . import ui_components

bl_info = {
    "name": "RealityCapture Metrics",
    "author": "Your Name",
    "version": (1, 1),
    "blender": (2, 93, 0),
    "location": "View3D > Sidebar > RC Metrics",
    "description": "Import RealityCapture results and calculate metrics",
    "warning": "",
    "doc_url": "",
    "category": "3D View",
}

# RealityCapture Metrics Property Group
class RCMetricsProperties(PropertyGroup):
    rc_folder: StringProperty(
        name="RC Result Folder",
        description="Path to the RealityCapture result folder",
        default="",
        subtype='DIR_PATH'
    )
    
    metrics_output: StringProperty(
        name="Metrics Output",
        description="Path to save the metrics results",
        default="",
        subtype='DIR_PATH'
    )
    
    # Camera list and selection
    cameras: CollectionProperty(type=camera_utils.RCCamera)
    active_camera_index: IntProperty(default=0)
    
    # Rendering options
    save_renders: BoolProperty(
        name="Save Renders",
        description="Save rendered images to disk",
        default=True
    )
    
    render_quality: EnumProperty(
        name="Render Quality",
        description="Quality settings for rendering",
        items=[
            ('preview', "Preview", "Fast, low-quality rendering (32 samples)"),
            ('medium', "Medium", "Balanced rendering (64 samples)"),
            ('high', "High", "High-quality rendering (128 samples)"),
            ('final', "Final", "Production-quality rendering (256 samples)"),
        ],
        default='preview'
    )
    
    # Threshold settings
    psnr_threshold: FloatProperty(
        name="PSNR Threshold",
        description="Minimum acceptable PSNR value",
        default=30.0,
        min=0.0,
        soft_max=50.0
    )
    
    ssim_threshold: FloatProperty(
        name="SSIM Threshold",
        description="Minimum acceptable SSIM value",
        default=0.9,
        min=0.0,
        max=1.0
    )
    
    # Calculation progress
    is_calculating: BoolProperty(default=False)
    calculation_progress: FloatProperty(default=0.0, min=0.0, max=100.0)
    current_camera: StringProperty(default="")
    
    # Results
    has_results: BoolProperty(default=False)
    average_psnr: FloatProperty(default=0.0)
    average_ssim: FloatProperty(default=0.0)

class RCMETRICS_OT_ImportRC(bpy.types.Operator):
    """Import RealityCapture results and setup cameras"""
    bl_idname = "rcmetrics.import_rc"
    bl_label = "1. Import RC & Setup"
    bl_options = {'REGISTER', 'UNDO'}
    
    def check_rc_folder_structure(self, folder_path):
        """Check if the folder has the expected RealityCapture structure"""
        # Check if the folder exists
        if not os.path.exists(folder_path):
            self.report({'ERROR'}, f"Folder does not exist: {folder_path}")
            return False
            
        # Check for .abc file
        abc_files = [f for f in os.listdir(folder_path) if f.endswith('.abc')]
        if not abc_files:
            self.report({'ERROR'}, "No .abc file found in the folder")
            return False
            
        # Check for image files (should be at least a few)
        png_files = [f for f in os.listdir(folder_path) if f.endswith('.png') and not f.endswith('_diffuse.png')]
        if len(png_files) < 2:
            self.report({'ERROR'}, "Not enough image files found in the folder")
            return False
            
        # Check for texture file
        texture_files = [f for f in os.listdir(folder_path) if f.endswith('_diffuse.png')]
        if not texture_files:
            self.report({'WARNING'}, "No texture file found, but proceeding anyway")
            
        return True, abc_files[0], png_files, texture_files[0] if texture_files else None
    
    def import_abc(self, abc_path):
        """Import the .abc file"""
        bpy.ops.wm.alembic_import(filepath=abc_path, as_background_job=False)
        # Return the name of the root collection from the import
        for collection in bpy.data.collections:
            if collection.name != "Collection" and collection.name != "Scene Collection":
                return collection.name
        return None
        
    def setup_cameras(self, folder_path, png_files):
        """Setup the virtual cameras with correct resolution and background"""
        # Get the first image to determine resolution
        first_img_path = os.path.join(folder_path, png_files[0])
        try:
            img = cv2.imread(first_img_path)
            if img is None:
                self.report({'ERROR'}, f"Could not read image: {first_img_path}")
                return False
                
            height, width, _ = img.shape
        except Exception as e:
            self.report({'ERROR'}, f"Error reading image: {e}")
            return False
        
        # Process all cameras
        for cam_obj in bpy.data.objects:
            if cam_obj.type == 'CAMERA':
                # Check if this camera corresponds to one of our image files
                cam_name = cam_obj.name
                if cam_name in png_files:
                    # Set camera resolution
                    scene = bpy.context.scene
                    scene.render.resolution_x = width
                    scene.render.resolution_y = height
                    
                    # Load the image
                    img_path = os.path.join(folder_path, cam_name)
                    try:
                        img = bpy.data.images.load(img_path, check_existing=True)
                    except:
                        self.report({'WARNING'}, f"Could not load image: {img_path}")
                        continue
                    
                    # Set up background image for the camera
                    cam_data = cam_obj.data
                    cam_data.show_background_images = True
                    
                    # Remove any existing background images
                    for bg in cam_data.background_images:
                        cam_data.background_images.remove(bg)
                    
                    # Add new background image
                    bg = cam_data.background_images.new()
                    bg.image = img
                    bg.alpha = 1.0
        
        return True
    
    def apply_texture(self, folder_path, texture_file, geometry_name="geometry"):
        """Apply texture to the geometry"""
        if not texture_file:
            return False
            
        # Find the geometry object
        geom_obj = None
        for obj in bpy.data.objects:
            if obj.name.lower() == geometry_name.lower() or "geom" in obj.name.lower():
                geom_obj = obj
                break
                
        if not geom_obj:
            self.report({'WARNING'}, "Geometry object not found, could not apply texture")
            return False
            
        # Load texture
        texture_path = os.path.join(folder_path, texture_file)
        try:
            tex_img = bpy.data.images.load(texture_path, check_existing=True)
        except:
            self.report({'ERROR'}, f"Could not load texture: {texture_path}")
            return False
            
        # Create material if needed
        if not geom_obj.data.materials:
            mat = bpy.data.materials.new(name="RC_Material")
            geom_obj.data.materials.append(mat)
        else:
            mat = geom_obj.data.materials[0]
            
        # Setup material
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        
        # Clear existing nodes
        for node in nodes:
            nodes.remove(node)
            
        # Create basic PBR setup
        output_node = nodes.new(type='ShaderNodeOutputMaterial')
        bsdf_node = nodes.new(type='ShaderNodeBsdfPrincipled')
        tex_node = nodes.new(type='ShaderNodeTexImage')
        
        # Position nodes
        output_node.location = (300, 0)
        bsdf_node.location = (0, 0)
        tex_node.location = (-300, 0)
        
        # Connect nodes
        links.new(bsdf_node.outputs['BSDF'], output_node.inputs['Surface'])
        links.new(tex_node.outputs['Color'], bsdf_node.inputs['Base Color'])
        
        # Assign texture
        tex_node.image = tex_img
        
        return True
    
    def execute(self, context):
        import cv2  # Import here to avoid issues if not installed
        
        folder_path = context.scene.rc_metrics.rc_folder
        
        # Validate folder path
        if not folder_path:
            self.report({'ERROR'}, "Please specify a RealityCapture result folder")
            return {'CANCELLED'}
            
        # Check folder structure
        check_result = self.check_rc_folder_structure(folder_path)
        if not check_result:
            return {'CANCELLED'}
            
        valid, abc_file, png_files, texture_file = check_result
        
        # Import ABC file
        abc_path = os.path.join(folder_path, abc_file)
        self.report({'INFO'}, f"Importing ABC file: {abc_path}")
        collection_name = self.import_abc(abc_path)
        
        if not collection_name:
            self.report({'WARNING'}, "Could not determine imported collection name")
            
        # Setup cameras
        self.report({'INFO'}, "Setting up cameras...")
        if not self.setup_cameras(folder_path, png_files):
            self.report({'ERROR'}, "Failed to setup cameras")
            return {'CANCELLED'}
            
        # Apply texture if available
        if texture_file:
            self.report({'INFO'}, f"Applying texture: {texture_file}")
            self.apply_texture(folder_path, texture_file)
        
        # Update camera list for the UI
        camera_utils.update_camera_list(context)
        
        self.report({'INFO'}, "RealityCapture import and setup completed")
        return {'FINISHED'}

class RCMETRICS_OT_CalculateMetrics(bpy.types.Operator):
    """Render current mesh from selected cameras and calculate metrics"""
    bl_idname = "rcmetrics.calculate_metrics"
    bl_label = "2. Calculate Metrics"
    bl_options = {'REGISTER', 'UNDO'}
    
    _timer = None
    _camera_queue = []
    _metrics_summary = {}
    
    def modal(self, context, event):
        """Modal function for handling the metrics calculation"""
        rc_metrics = context.scene.rc_metrics
        
        # Check if calculation should be cancelled
        if not rc_metrics.is_calculating:
            self.cancel(context)
            return {'CANCELLED'}
            
        # Process timer events
        if event.type == 'TIMER':
            # If we have cameras to process
            if self._camera_queue:
                # Get the next camera
                camera = self._camera_queue.pop(0)
                rc_metrics.current_camera = camera.name
                
                # Update progress
                progress = 100.0 * (1.0 - len(self._camera_queue) / self._total_cameras)
                rc_metrics.calculation_progress = progress
                
                # Process this camera
                self.process_camera(context, camera)
                
                # Force UI update
                for area in context.screen.areas:
                    area.tag_redraw()
                
                # We're still processing, continue modal
                return {'RUNNING_MODAL'}
            else:
                # We're done, finalize and finish
                self.finish_calculation(context)
                
                # Force UI update once more before finishing
                for area in context.screen.areas:
                    area.tag_redraw()
                
                return {'FINISHED'}
                
        # Continue running modal
        return {'RUNNING_MODAL'}
    
    def invoke(self, context, event):
        """Start the modal timer"""
        # Check active object
        if not context.active_object or context.active_object.type != 'MESH':
            self.report({'ERROR'}, "Please select a mesh object to evaluate")
            return {'CANCELLED'}
            
        # Get folder paths
        rc_metrics = context.scene.rc_metrics
        
        if not rc_metrics.metrics_output and rc_metrics.save_renders:
            # Create a default output folder if not specified
            rc_metrics.metrics_output = os.path.join(rc_metrics.rc_folder, "metrics_output")
            try:
                os.makedirs(rc_metrics.metrics_output, exist_ok=True)
            except:
                self.report({'ERROR'}, f"Could not create output directory: {rc_metrics.metrics_output}")
                return {'CANCELLED'}
        
        # Get enabled cameras
        self._camera_queue = camera_utils.get_enabled_cameras(context)
        
        if not self._camera_queue:
            self.report({'ERROR'}, "No cameras selected for calculation")
            return {'CANCELLED'}
            
        # Initialize calculation
        self._total_cameras = len(self._camera_queue)
        self._metrics_summary = {
            "mesh_name": context.active_object.name,
            "cameras": [],
            "average_psnr": 0.0,
            "average_ssim": 0.0,
            "min_psnr": float('inf'),
            "min_ssim": float('inf'),
            "max_psnr": 0.0,
            "max_ssim": 0.0
        }
        
        # Setup render settings
        render_utils.setup_render_settings(context, rc_metrics.render_quality)
        
        # Create render output if saving renders
        if rc_metrics.save_renders:
            self._render_output = os.path.join(rc_metrics.metrics_output, "renders")
            try:
                os.makedirs(self._render_output, exist_ok=True)
            except:
                self.report({'ERROR'}, f"Could not create render output directory: {self._render_output}")
                return {'CANCELLED'}
        else:
            self._render_output = None
        
        # Start modal timer
        # Increase timer interval to 2.0 seconds to give more time for UI updates
        self._timer = context.window_manager.event_timer_add(2.0, window=context.window)
        context.window_manager.modal_handler_add(self)
        
        # Set calculation in progress
        rc_metrics.is_calculating = True
        rc_metrics.calculation_progress = 0.0
        rc_metrics.has_results = False
        
        self.report({'INFO'}, f"Starting calculation for {self._total_cameras} cameras")
        return {'RUNNING_MODAL'}
    
    def process_camera(self, context, camera):
        """Process a single camera"""
        rc_metrics = context.scene.rc_metrics
        
        # Render from this camera
        if rc_metrics.save_renders:
            render_img_path = os.path.join(self._render_output, f"{camera.name.split('.')[0]}_render.png")
            self.report({'INFO'}, f"Rendering from camera: {camera.name}")
            rendered_img = render_utils.render_from_camera(context, camera, render_img_path)
        else:
            self.report({'INFO'}, f"Processing camera: {camera.name}")
            rendered_img = render_utils.render_from_camera(context, camera, None)
        
        # Get the reference image
        ref_img = render_utils.get_camera_background_image(camera)
        
        # Calculate metrics
        if ref_img is not None and rendered_img is not None:
            psnr, ssim = render_utils.calculate_image_metrics(ref_img, rendered_img)
            
            if psnr is not None and ssim is not None:
                # Update metrics summary
                self._metrics_summary = render_utils.update_metrics_summary(
                    self._metrics_summary, camera.name, psnr, ssim)
                
                # Update UI list
                result = camera_utils.update_camera_results(context, camera.name, psnr, ssim, 
                                                  rc_metrics.psnr_threshold, rc_metrics.ssim_threshold)
                
                # Debug info
                if not result:
                    self.report({'WARNING'}, f"Failed to update UI for camera: {camera.name}")
                
                # Report results
                self.report({'INFO'}, f"Camera: {camera.name}, PSNR: {psnr:.2f}, SSIM: {ssim:.4f}")
                
                # Update averages in the UI
                rc_metrics.average_psnr = self._metrics_summary["average_psnr"]
                rc_metrics.average_ssim = self._metrics_summary["average_ssim"]
                rc_metrics.has_results = True
                
                return True
            
        self.report({'WARNING'}, f"Could not calculate metrics for camera: {camera.name}")
        return False
    
    def finish_calculation(self, context):
        """Finish the calculation and clean up"""
        rc_metrics = context.scene.rc_metrics
        
        # Save metrics to file if we have results and are saving renders
        if rc_metrics.has_results and rc_metrics.save_renders:
            metrics_file = os.path.join(rc_metrics.metrics_output, 
                                        f"metrics_{self._metrics_summary['mesh_name']}.json")
            with open(metrics_file, 'w') as f:
                json.dump(self._metrics_summary, f, indent=4)
                
            self.report({'INFO'}, f"Metrics saved to: {metrics_file}")
        
        # Clean up
        rc_metrics.is_calculating = False
        rc_metrics.calculation_progress = 100.0
        rc_metrics.current_camera = ""
        
        camera_count = len(self._metrics_summary.get("cameras", []))
        self.report({'INFO'}, f"Calculation completed for {camera_count} cameras")
        self.report({'INFO'}, f"Average PSNR: {rc_metrics.average_psnr:.2f}, Average SSIM: {rc_metrics.average_ssim:.4f}")
        
        # Show results for cameras where update_camera_results failed
        for cam_info in self._metrics_summary.get("cameras", []):
            camera_name = cam_info["camera"]
            psnr = cam_info["psnr"]
            ssim = cam_info["ssim"]
            print(f"Results for {camera_name}: PSNR={psnr:.2f}, SSIM={ssim:.4f}")
        
        # Force a final UI update
        for area in context.screen.areas:
            area.tag_redraw()
    
    def cancel(self, context):
        """Cancel the calculation"""
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None
            
        # Clean up
        context.scene.rc_metrics.is_calculating = False
        context.scene.rc_metrics.current_camera = ""
        
        self.report({'INFO'}, "Calculation cancelled")

class RCMETRICS_PT_Panel(bpy.types.Panel):
    """RC Metrics Panel"""
    bl_label = "RC Metrics"
    bl_idname = "RCMETRICS_PT_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'RC Metrics'
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        rc_metrics = scene.rc_metrics
        
        layout.label(text="RealityCapture Import & Metrics")
        
        box = layout.box()
        box.label(text="1. Import and Setup")
        box.prop(rc_metrics, "rc_folder")
        box.operator("rcmetrics.import_rc")
        
        box = layout.box()
        box.label(text="2. Calculate Metrics")
        box.label(text="Select a mesh to evaluate:")
        
        # Show active object
        if context.active_object and context.active_object.type == 'MESH':
            box.label(text=f"Current: {context.active_object.name}", icon='MESH_DATA')
        else:
            box.label(text="No mesh selected", icon='ERROR')
            
        box.prop(rc_metrics, "metrics_output")
        
        # Show calculate button only if not currently calculating
        if not rc_metrics.is_calculating:
            box.operator("rcmetrics.calculate_metrics")
        
        # Add Debug button
        box = layout.box()
        box.label(text="Debug Tools")
        box.operator("rcmetrics.refresh_ui", text="Refresh UI", icon='FILE_REFRESH')
        
        # Show summary of results if available
        if rc_metrics.has_results and not rc_metrics.is_calculating:
            row = box.row()
            row.label(text=f"PSNR: {rc_metrics.average_psnr:.2f}")
            row.label(text=f"SSIM: {rc_metrics.average_ssim:.4f}")

def register():
    # Register classes
    bpy.utils.register_class(camera_utils.RCCamera)
    bpy.utils.register_class(camera_utils.RCMETRICS_UL_CamerasList)
    bpy.utils.register_class(RCMetricsProperties)
    bpy.utils.register_class(RCMETRICS_OT_ImportRC)
    bpy.utils.register_class(RCMETRICS_OT_CalculateMetrics)
    bpy.utils.register_class(RCMETRICS_PT_Panel)
    
    # Register UI components
    ui_components.register_ui()
    
    # Register properties
    bpy.types.Scene.rc_metrics = bpy.props.PointerProperty(type=RCMetricsProperties)
    
def unregister():
    # Unregister UI components
    ui_components.unregister_ui()
    
    # Unregister classes
    bpy.utils.unregister_class(RCMETRICS_PT_Panel)
    bpy.utils.unregister_class(RCMETRICS_OT_CalculateMetrics)
    bpy.utils.unregister_class(RCMETRICS_OT_ImportRC)
    bpy.utils.unregister_class(RCMetricsProperties)
    bpy.utils.unregister_class(camera_utils.RCMETRICS_UL_CamerasList)
    bpy.utils.unregister_class(camera_utils.RCCamera)
    
    # Unregister properties
    del bpy.types.Scene.rc_metrics
    
if __name__ == "__main__":
    register()
