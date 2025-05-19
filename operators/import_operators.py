"""
Import operators for RC Metrics Add-on.
This module handles importing RealityCapture results.
"""

import bpy
import os
from bpy.props import StringProperty

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
        # Import needed modules here to avoid issues if not installed
        import cv2
        
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
            
        # Create Emission shader setup
        output_node = nodes.new(type='ShaderNodeOutputMaterial')
        emission_node = nodes.new(type='ShaderNodeEmission')
        tex_node = nodes.new(type='ShaderNodeTexImage')
        
        # Position nodes
        output_node.location = (300, 0)
        emission_node.location = (0, 0)
        tex_node.location = (-300, 0)
        
        # Connect nodes
        links.new(emission_node.outputs['Emission'], output_node.inputs['Surface'])
        links.new(tex_node.outputs['Color'], emission_node.inputs['Color'])
        
        # Set emission strength
        emission_node.inputs['Strength'].default_value = 1.0
        
        # Assign texture
        tex_node.image = tex_img
        
        return True
    
    def execute(self, context):
        try:
            # Import here to avoid issues if not installed
            import cv2
        except ImportError:
            self.report({'ERROR'}, "Cannot import OpenCV (cv2). Please install the required dependencies.")
            return {'CANCELLED'}
        
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

# Registration
def register():
    bpy.utils.register_class(RCMETRICS_OT_ImportRC)

def unregister():
    bpy.utils.unregister_class(RCMETRICS_OT_ImportRC)
