"""
Camera panel UI for RC Metrics Add-on.
"""

import bpy
from bpy.types import Panel

class RCMETRICS_PT_CameraPanel(Panel):
    """Camera Selection Panel"""
    bl_label = "Camera Selection"
    bl_idname = "RCMETRICS_PT_CameraPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'RC Metrics'
    bl_parent_id = "RCMETRICS_PT_Panel"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        rc_metrics = context.scene.rc_metrics
        
        # Camera selection tools
        row = layout.row()
        row.operator("rcmetrics.refresh_cameras", text="Refresh List")
        
        # Show the camera list
        row = layout.row()
        row.template_list("RCMETRICS_UL_CamerasList", "", rc_metrics, "cameras", 
                         rc_metrics, "active_camera_index", rows=5)
        
        # Add button to select active camera
        row = layout.row()
        row.operator("rcmetrics.select_camera", text="Select This Camera")
        
        # Add button to view through camera
        row = layout.row()
        row.operator("rcmetrics.view_through_camera", text="Look Through Camera")
        
        # Add button to reset view
        row = layout.row()
        row.operator("rcmetrics.reset_view", text="Reset View", icon='LOOP_BACK')
        
        # Show stats
        if len(rc_metrics.cameras) > 0:
            layout.label(text=f"Total: {len(rc_metrics.cameras)} cameras")
            
            # Count enabled cameras
            enabled_count = sum(1 for cam in rc_metrics.cameras if cam.enabled)
            if enabled_count > 0:
                layout.label(text=f"Selected: Camera {rc_metrics.cameras[rc_metrics.active_camera_index].name}")
            
            # Count cameras with results
            results_count = sum(1 for cam in rc_metrics.cameras if cam.has_results)
            if results_count > 0:
                layout.label(text=f"Cameras with results: {results_count}")
        
        # Add refresh UI button
        layout.operator("rcmetrics.refresh_ui", text="Refresh UI", icon='FILE_REFRESH')

# Registration
def register():
    bpy.utils.register_class(RCMETRICS_PT_CameraPanel)

def unregister():
    bpy.utils.unregister_class(RCMETRICS_PT_CameraPanel)
