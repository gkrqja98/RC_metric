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
        
        # Camera rendering and comparison section
        layout.separator()
        layout.label(text="Camera Rendering & Metrics")
        
        box = layout.box()
        
        # Camera selector dropdown
        box.prop(rc_metrics, "selected_camera")
        
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
        
        # Render and compare button
        row = box.row()
        row.operator("rcmetrics.render_compare", icon='RENDER_STILL')
        
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
