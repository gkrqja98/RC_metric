"""
Camera operators for RC Metrics Add-on.
This module handles camera selection and management.
"""

import bpy
from bpy.props import BoolProperty, IntProperty

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

class RCMETRICS_OT_SelectCamera(bpy.types.Operator):
    """Select a specific camera for metrics calculation"""
    bl_idname = "rcmetrics.select_camera"
    bl_label = "Select Camera"
    bl_options = {'REGISTER', 'UNDO'}
    
    camera_index: IntProperty(default=-1)
    
    def execute(self, context):
        from ..utils import camera_utils
        
        if self.camera_index == -1:
            # Use the active camera index
            self.camera_index = context.scene.rc_metrics.active_camera_index
        
        camera_name = camera_utils.select_single_camera(context, self.camera_index)
        
        if camera_name:
            self.report({'INFO'}, f"Selected camera: {camera_name}")
            # Set the active camera in the viewport
            camera_obj = bpy.data.objects.get(camera_name)
            if camera_obj:
                context.view_layer.objects.active = camera_obj
                # Optionally set the view to camera view
                # bpy.ops.view3d.view_camera()
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "No camera selected")
            return {'CANCELLED'}

class RCMETRICS_OT_ViewThroughCamera(bpy.types.Operator):
    """Set the view to look through the selected camera"""
    bl_idname = "rcmetrics.view_through_camera"
    bl_label = "View Through Camera"
    bl_options = {'REGISTER', 'UNDO'}
    
    hide_other_objects: BoolProperty(
        name="Hide Other Objects",
        description="Hide all objects except the selected mesh",
        default=True
    )
    
    def execute(self, context):
        rc_metrics = context.scene.rc_metrics
        
        # Check if we have an active camera
        if len(rc_metrics.cameras) == 0 or rc_metrics.active_camera_index < 0:
            self.report({'ERROR'}, "No active camera selected")
            return {'CANCELLED'}
        
        # Get the camera name
        camera_name = rc_metrics.cameras[rc_metrics.active_camera_index].name
        
        # Get the camera object
        camera_obj = bpy.data.objects.get(camera_name)
        if camera_obj and camera_obj.type == 'CAMERA':
            # Set as scene camera
            context.scene.camera = camera_obj
            
            # If requested, hide other objects except the active mesh
            if self.hide_other_objects and context.active_object and context.active_object.type == 'MESH':
                active_mesh = context.active_object
                
                # Save current visibility state to restore later
                self._visibility_state = {}
                for obj in bpy.data.objects:
                    self._visibility_state[obj.name] = obj.hide_viewport
                    
                    # Hide everything except the active mesh and camera
                    if obj != active_mesh and obj != camera_obj:
                        obj.hide_viewport = True
                    else:
                        obj.hide_viewport = False
                
                self.report({'INFO'}, f"Set view to camera and hid other objects")
            
            # Switch to camera view
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.spaces[0].region_3d.view_perspective = 'CAMERA'
                    break
            
            self.report({'INFO'}, f"Set view to camera: {camera_name}")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, f"Camera {camera_name} not found or not a camera")
            return {'CANCELLED'}

class RCMETRICS_OT_ResetView(bpy.types.Operator):
    """Reset the view and object visibility"""
    bl_idname = "rcmetrics.reset_view"
    bl_label = "Reset View"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Reset all object visibilities
        for obj in bpy.data.objects:
            obj.hide_viewport = False
            
        # Reset to user perspective
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces[0].region_3d.view_perspective = 'PERSP'
                break
        
        self.report({'INFO'}, "Reset view and object visibility")
        return {'FINISHED'}

# Registration
def register():
    bpy.utils.register_class(RCMETRICS_OT_RefreshCameras)
    bpy.utils.register_class(RCMETRICS_OT_SelectCamera)
    bpy.utils.register_class(RCMETRICS_OT_ViewThroughCamera)
    bpy.utils.register_class(RCMETRICS_OT_ResetView)

def unregister():
    bpy.utils.unregister_class(RCMETRICS_OT_ResetView)
    bpy.utils.unregister_class(RCMETRICS_OT_ViewThroughCamera)
    bpy.utils.unregister_class(RCMETRICS_OT_SelectCamera)
    bpy.utils.unregister_class(RCMETRICS_OT_RefreshCameras)
