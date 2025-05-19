"""
Camera operators for RC Metrics Add-on.
This module handles camera selection and management.
"""

import bpy
from bpy.props import BoolProperty

class RCMETRICS_OT_RefreshCameras(bpy.types.Operator):
    """Refresh the camera list"""
    bl_idname = "rcmetrics.refresh_cameras"
    bl_label = "Refresh Cameras"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        from ..utils import camera_utils
        count = camera_utils.update_camera_list(context)
        self.report({'INFO'}, f"Found {count} cameras")
        return {'FINISHED'}

class RCMETRICS_OT_SelectAllCameras(bpy.types.Operator):
    """Select all cameras in the list"""
    bl_idname = "rcmetrics.select_all_cameras"
    bl_label = "Select All Cameras"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        from ..utils import camera_utils
        count = camera_utils.select_all_cameras(context, True)
        self.report({'INFO'}, f"Selected {count} cameras")
        return {'FINISHED'}

class RCMETRICS_OT_DeselectAllCameras(bpy.types.Operator):
    """Deselect all cameras in the list"""
    bl_idname = "rcmetrics.deselect_all_cameras"
    bl_label = "Deselect All Cameras"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        from ..utils import camera_utils
        count = camera_utils.select_all_cameras(context, False)
        self.report({'INFO'}, f"Deselected {count} cameras")
        return {'FINISHED'}

# Registration
def register():
    bpy.utils.register_class(RCMETRICS_OT_RefreshCameras)
    bpy.utils.register_class(RCMETRICS_OT_SelectAllCameras)
    bpy.utils.register_class(RCMETRICS_OT_DeselectAllCameras)

def unregister():
    bpy.utils.unregister_class(RCMETRICS_OT_DeselectAllCameras)
    bpy.utils.unregister_class(RCMETRICS_OT_SelectAllCameras)
    bpy.utils.unregister_class(RCMETRICS_OT_RefreshCameras)
