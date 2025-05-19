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
        
        layout.label(text="RealityCapture Import & Setup")
        
        box = layout.box()
        box.label(text="1. Import and Setup")
        box.prop(rc_metrics, "rc_folder")
        box.operator("rcmetrics.import_rc")

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
