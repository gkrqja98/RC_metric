"""
Main panel UI for RC Metrics Add-on.
"""

import bpy
from bpy.types import Panel

class RCMETRICS_PT_Panel(Panel):
    """RC Metrics Main Panel"""
    bl_label = "RC Metrics"
    bl_idname = "RCMETRICS_PT_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'RC Metrics'
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        rc_metrics = scene.rc_metrics
        
        # Import section
        layout.label(text="RealityCapture Import")
        
        box = layout.box()
        box.label(text="Import and Setup")
        box.prop(rc_metrics, "rc_folder")
        box.operator("rcmetrics.import_rc")
        
        # Camera & Object Selection section
        layout.separator()
        layout.label(text="Camera & Object Selection", icon='GROUP_VERTEX')
        
        box = layout.box()
        
        # Camera selector dropdown
        box.prop(rc_metrics, "selected_camera")
        
        # Selection type (Mesh or Collection)
        box.prop(rc_metrics, "selection_type")
        
        # Mesh or Collection selector based on selection type
        if rc_metrics.selection_type == 'MESH':
            box.prop(rc_metrics, "selected_mesh")
        else:  # COLLECTION
            box.prop(rc_metrics, "selected_collection")
        
        # Option to render only selected mesh/collection
        box.prop(rc_metrics, "render_selected_only")
        
        # Check active camera and guide user
        if not scene.camera:
            box.label(text="No active camera selected!", icon='ERROR')
            box.label(text="Select a camera from the dropdown above")
        else:
            # Show active camera name
            box.label(text=f"Active Camera: {scene.camera.name}", icon='CAMERA_DATA')
            # Show camera background image status
            has_bg = False
            if hasattr(scene.camera.data, 'background_images'):
                for bg in scene.camera.data.background_images:
                    if bg.image:
                        has_bg = True
                        break
            
            if has_bg:
                box.label(text="Background image found", icon='IMAGE_DATA')
            else:
                box.label(text="No background image assigned", icon='ERROR')
        
        # Check if something valid is selected for rendering
        valid_selection = False
        if rc_metrics.selection_type == 'MESH':
            if rc_metrics.selected_mesh and rc_metrics.selected_mesh != 'None':
                mesh_obj = scene.objects.get(rc_metrics.selected_mesh)
                if mesh_obj and mesh_obj.type == 'MESH':
                    box.label(text=f"Selected Mesh: {mesh_obj.name}", icon='MESH_DATA')
                    valid_selection = True
                else:
                    box.label(text="Selected mesh not found!", icon='ERROR')
            else:
                box.label(text="No mesh selected", icon='ERROR')
        else:  # COLLECTION
            if rc_metrics.selected_collection and rc_metrics.selected_collection != 'None':
                collection = bpy.data.collections.get(rc_metrics.selected_collection)
                if collection:
                    box.label(text=f"Selected Collection: {collection.name}", icon='OUTLINER_COLLECTION')
                    
                    # Count meshes in collection
                    mesh_count = 0
                    for obj in collection.objects:
                        if obj.type == 'MESH':
                            mesh_count += 1
                    
                    # Also count meshes in child collections
                    for child_coll in collection.children_recursive:
                        for obj in child_coll.objects:
                            if obj.type == 'MESH':
                                mesh_count += 1
                    
                    if mesh_count > 0:
                        box.label(text=f"Collection contains {mesh_count} meshes", icon='INFO')
                        valid_selection = True
                    else:
                        box.label(text="No meshes in this collection!", icon='ERROR')
                else:
                    box.label(text="Selected collection not found!", icon='ERROR')
            else:
                box.label(text="No collection selected", icon='ERROR')
            
        # Render button (분리된 기능)
        row = box.row()
        if scene.camera and valid_selection:
            row.operator("rcmetrics.render", icon='RENDER_STILL')
            row.operator("rcmetrics.render_compare", icon='RENDER_RESULT')
        else:
            row.label(text="Select camera and a valid mesh/collection first", icon='INFO')
        
        # Compare section (새로운 섹션)
        layout.separator()
        layout.label(text="Image Comparison", icon='IMAGE_BACKGROUND')
        
        compare_box = layout.box()
        
        # Check if render exists before enabling compare
        render_exists = bpy.data.images.get("RC_Current_Render") is not None
        
        if not render_exists:
            compare_box.label(text="Render the scene first to enable comparison", icon='ERROR')
        
        # Compare mode selector
        compare_box.prop(rc_metrics, "compare_mode")
        
        # Edge thickness for edges-only mode
        if rc_metrics.compare_mode == 'EDGES_ONLY':
            compare_box.prop(rc_metrics, "edge_thickness")
        
        # Compare button
        row = compare_box.row()
        row.enabled = render_exists
        row.operator("rcmetrics.compare", icon='SHADERFX')
        
        # Display metrics if they exist
        if rc_metrics.last_psnr > 0 or rc_metrics.last_ssim > 0:
            metrics_box = layout.box()
            metrics_box.label(text="Image Comparison Results:", icon='INFO')
            col = metrics_box.column(align=True)
            col.label(text=f"PSNR: {rc_metrics.last_psnr:.2f} dB")
            col.label(text=f"SSIM: {rc_metrics.last_ssim:.4f}")
            
            # Add buttons to view rendered and difference images
            box = layout.box()
            box.label(text="View Results:", icon='IMAGE_DATA')
            
            row = box.row()
            row.operator("rcmetrics.view_render", text="View Render", icon='RENDER_RESULT')
            row.operator("rcmetrics.view_diff", text="View Difference", icon='DRIVER_DISTANCE')
            
            # Add button to view edge mask if in edge mode
            if rc_metrics.compare_mode == 'EDGES_ONLY' and bpy.data.images.get("RC_Edge_Mask") is not None:
                row = box.row()
                row.operator("rcmetrics.view_edge_mask", text="View Edge Mask", icon='MESH_DATA')
            
            # Difference visualization options
            diff_box = layout.box()
            diff_box.label(text="Difference Visualization Options:", icon='OPTIONS')
            diff_box.prop(rc_metrics, "diff_view_mode")
            diff_box.prop(rc_metrics, "diff_multiplier", slider=True)
            
            # Add guidance on interpreting results
            info_box = layout.box()
            info_box.label(text="Metrics Interpretation:", icon='QUESTION')
            col = info_box.column(align=True)
            col.label(text="PSNR > 30dB: Good quality")
            col.label(text="SSIM > 0.9: High similarity")
            col.label(text="SSIM > 0.95: Excellent match")

# Registration
def register():
    bpy.utils.register_class(RCMETRICS_PT_Panel)

def unregister():
    bpy.utils.unregister_class(RCMETRICS_PT_Panel)
