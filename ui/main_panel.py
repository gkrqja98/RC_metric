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
        
        layout.label(text="RealityCapture Import")
        
        box = layout.box()
        box.label(text="Import and Setup")
        box.prop(rc_metrics, "rc_folder")
        box.operator("rcmetrics.import_rc")

# Registration
def register():
    bpy.utils.register_class(RCMETRICS_PT_Panel)

def unregister():
    bpy.utils.unregister_class(RCMETRICS_PT_Panel)
