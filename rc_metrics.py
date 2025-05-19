bl_info = {
    "name": "RealityCapture Metrics",
    "author": "Claude",
    "version": (1, 0),
    "blender": (2, 93, 0),
    "location": "View3D > Sidebar > RC Metrics",
    "description": "Import RealityCapture results and calculate metrics",
    "warning": "",
    "doc_url": "",
    "category": "3D View",
}

import bpy
import os
import numpy as np
from mathutils import Vector
import math
from skimage.metrics import structural_similarity, peak_signal_noise_ratio
import cv2
import json

class RCMetricsProperties(bpy.types.PropertyGroup):
    rc_folder: bpy.props.StringProperty(
        name="RC Result Folder",
        description="Path to the RealityCapture result folder",
        default="",
        subtype='DIR_PATH'
    )
    
    metrics_output: bpy.props.StringProperty(
        name="Metrics Output",
        description="Path to save the metrics results",
        default="",
        subtype='DIR_PATH'
    )

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
        
        self.report({'INFO'}, "RealityCapture import and setup completed")
        return {'FINISHED'}

class RCMETRICS_OT_CalculateMetrics(bpy.types.Operator):
    """Render current mesh from all cameras and calculate metrics"""
    bl_idname = "rcmetrics.calculate_metrics"
    bl_label = "2. Calculate Metrics"
    bl_options = {'REGISTER', 'UNDO'}
    
    def setup_render_settings(self, context):
        """Setup render settings for evaluation"""
        scene = context.scene
        # Set render engine
        scene.render.engine = 'CYCLES'
        # Set render settings for faster preview quality
        scene.cycles.samples = 32
        scene.render.resolution_percentage = 100
        # Disable film transparency so we get just the render
        scene.render.film_transparent = False
        
    def render_from_camera(self, context, camera, output_path):
        """Render the scene from a specific camera and save the image"""
        scene = context.scene
        scene.camera = camera
        
        # Store original filepath
        original_filepath = scene.render.filepath
        
        # Set output path for this render
        scene.render.filepath = output_path
        
        # Render
        bpy.ops.render.render(write_still=True)
        
        # Restore original filepath
        scene.render.filepath = original_filepath
        
        return True
    
    def calculate_image_metrics(self, ref_img_path, rendered_img_path):
        """Calculate PSNR and SSIM between two images"""
        try:
            # Read images
            ref_img = cv2.imread(ref_img_path)
            rendered_img = cv2.imread(rendered_img_path)
            
            if ref_img is None:
                raise ValueError(f"Could not read reference image: {ref_img_path}")
            if rendered_img is None:
                raise ValueError(f"Could not read rendered image: {rendered_img_path}")
                
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
    
    def execute(self, context):
        # Ensure we have an active object (the mesh to evaluate)
        if not context.active_object or context.active_object.type != 'MESH':
            self.report({'ERROR'}, "Please select a mesh object to evaluate")
            return {'CANCELLED'}
            
        # Get folder paths
        rc_folder = context.scene.rc_metrics.rc_folder
        metrics_output = context.scene.rc_metrics.metrics_output
        
        if not metrics_output:
            # Create a default output folder if not specified
            metrics_output = os.path.join(rc_folder, "metrics_output")
            try:
                os.makedirs(metrics_output, exist_ok=True)
            except:
                self.report({'ERROR'}, f"Could not create output directory: {metrics_output}")
                return {'CANCELLED'}
        
        # Setup render settings
        self.setup_render_settings(context)
        
        # Create results folder
        render_output = os.path.join(metrics_output, "renders")
        try:
            os.makedirs(render_output, exist_ok=True)
        except:
            self.report({'ERROR'}, f"Could not create render output directory: {render_output}")
            return {'CANCELLED'}
        
        # Get selected mesh object
        mesh_obj = context.active_object
        
        # Prepare to collect metrics
        metrics_results = {}
        metrics_summary = {
            "mesh_name": mesh_obj.name,
            "cameras": [],
            "average_psnr": 0.0,
            "average_ssim": 0.0,
            "min_psnr": float('inf'),
            "min_ssim": float('inf'),
            "max_psnr": 0.0,
            "max_ssim": 0.0
        }
        
        total_psnr = 0.0
        total_ssim = 0.0
        valid_cameras = 0
        
        # Process all cameras
        for obj in bpy.data.objects:
            if obj.type == 'CAMERA':
                cam_name = obj.name
                # Check if this camera has a matching background image
                if not obj.data.background_images or not obj.data.background_images[0].image:
                    continue
                    
                # Get the reference image path
                ref_img_name = cam_name
                ref_img_path = os.path.join(rc_folder, ref_img_name)
                
                if not os.path.exists(ref_img_path):
                    self.report({'WARNING'}, f"Reference image does not exist: {ref_img_path}")
                    continue
                
                # Render from this camera
                render_img_path = os.path.join(render_output, f"{cam_name.split('.')[0]}_render.png")
                self.report({'INFO'}, f"Rendering from camera: {cam_name}")
                
                if not self.render_from_camera(context, obj, render_img_path):
                    self.report({'WARNING'}, f"Failed to render from camera: {cam_name}")
                    continue
                
                # Calculate metrics
                psnr, ssim = self.calculate_image_metrics(ref_img_path, render_img_path)
                
                if psnr is not None and ssim is not None:
                    # Store results
                    metrics_results[cam_name] = {
                        "psnr": psnr,
                        "ssim": ssim,
                        "reference": ref_img_path,
                        "render": render_img_path
                    }
                    
                    # Update summary
                    total_psnr += psnr
                    total_ssim += ssim
                    valid_cameras += 1
                    
                    metrics_summary["min_psnr"] = min(metrics_summary["min_psnr"], psnr)
                    metrics_summary["min_ssim"] = min(metrics_summary["min_ssim"], ssim)
                    metrics_summary["max_psnr"] = max(metrics_summary["max_psnr"], psnr)
                    metrics_summary["max_ssim"] = max(metrics_summary["max_ssim"], ssim)
                    
                    metrics_summary["cameras"].append({
                        "camera": cam_name,
                        "psnr": psnr,
                        "ssim": ssim
                    })
                    
                    self.report({'INFO'}, f"Camera: {cam_name}, PSNR: {psnr:.2f}, SSIM: {ssim:.4f}")
        
        # Calculate averages
        if valid_cameras > 0:
            metrics_summary["average_psnr"] = total_psnr / valid_cameras
            metrics_summary["average_ssim"] = total_ssim / valid_cameras
            
            # Save metrics to file
            metrics_file = os.path.join(metrics_output, f"metrics_{mesh_obj.name}.json")
            with open(metrics_file, 'w') as f:
                json.dump(metrics_summary, f, indent=4)
                
            self.report({'INFO'}, f"Metrics calculated for {valid_cameras} cameras")
            self.report({'INFO'}, f"Average PSNR: {metrics_summary['average_psnr']:.2f}, Average SSIM: {metrics_summary['average_ssim']:.4f}")
            self.report({'INFO'}, f"Metrics saved to: {metrics_file}")
        else:
            self.report({'ERROR'}, "No valid cameras processed")
            return {'CANCELLED'}
        
        return {'FINISHED'}

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
        box.operator("rcmetrics.calculate_metrics")

def register():
    bpy.utils.register_class(RCMetricsProperties)
    bpy.utils.register_class(RCMETRICS_OT_ImportRC)
    bpy.utils.register_class(RCMETRICS_OT_CalculateMetrics)
    bpy.utils.register_class(RCMETRICS_PT_Panel)
    bpy.types.Scene.rc_metrics = bpy.props.PointerProperty(type=RCMetricsProperties)
    
def unregister():
    bpy.utils.unregister_class(RCMETRICS_PT_Panel)
    bpy.utils.unregister_class(RCMETRICS_OT_CalculateMetrics)
    bpy.utils.unregister_class(RCMETRICS_OT_ImportRC)
    bpy.utils.unregister_class(RCMetricsProperties)
    del bpy.types.Scene.rc_metrics
    
if __name__ == "__main__":
    register()
