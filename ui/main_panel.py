"""
Main panel UI for RC Metrics Add-on.
"""

import bpy
from bpy.types import Panel, Operator

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
            
        # Show selected camera
        enabled_cameras = [cam for cam in rc_metrics.cameras if cam.enabled]
        if enabled_cameras:
            box.label(text=f"Selected camera: {enabled_cameras[0].name}", icon='CAMERA_DATA')
        else:
            box.label(text="No camera selected", icon='ERROR')
            box.label(text="Select a camera in Camera Selection panel")
            
        box.prop(rc_metrics, "metrics_output")
        
        # Show calculate button only if not currently calculating
        if not rc_metrics.is_calculating:
            box.operator("rcmetrics.calculate_metrics")
        
        # Show summary of results if available
        if rc_metrics.has_results and not rc_metrics.is_calculating:
            row = box.row()
            row.label(text=f"PSNR: {rc_metrics.average_psnr:.2f}")
            row.label(text=f"SSIM: {rc_metrics.average_ssim:.4f}")
            
            # Add export buttons
            box.operator("rcmetrics.export_results", text="Export JSON", icon='FILE_TICK')
            box.operator("rcmetrics.export_report", text="Export HTML Report", icon='TEXT')

class RCMETRICS_OT_RefreshUI(Operator):
    """Refresh the UI to show updated results"""
    bl_idname = "rcmetrics.refresh_ui"
    bl_label = "Refresh UI"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Force a redraw of all UI areas
        for area in context.screen.areas:
            area.tag_redraw()
            
        # Print debug info
        rc_metrics = context.scene.rc_metrics
        results_count = sum(1 for cam in rc_metrics.cameras if cam.has_results)
        self.report({'INFO'}, f"UI refreshed. {results_count} cameras have results.")
        
        return {'FINISHED'}

# Registration
def register():
    bpy.utils.register_class(RCMETRICS_PT_Panel)
    bpy.utils.register_class(RCMETRICS_OT_RefreshUI)

def unregister():
    bpy.utils.unregister_class(RCMETRICS_OT_RefreshUI)
    bpy.utils.unregister_class(RCMETRICS_PT_Panel)
