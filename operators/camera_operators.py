import bpy
import os
from bpy.props import BoolProperty

class RCMETRICS_OT_PopulateCameraList(bpy.types.Operator):
    """Populate the camera list based on scene cameras"""
    bl_idname = "rcmetrics.populate_camera_list"
    bl_label = "Refresh Camera List"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        rc_metrics = context.scene.rc_metrics
        
        # Clear the current camera list
        rc_metrics.cameras.clear()
        
        # Find all cameras in the scene
        for obj in bpy.data.objects:
            if obj.type == 'CAMERA':
                # Check if the camera has a background image
                has_bg = obj.data.background_images and obj.data.background_images[0].image
                
                if has_bg:
                    # Add to the camera list
                    item = rc_metrics.cameras.add()
                    item.name = obj.name
                    item.camera = obj
                    item.selected = rc_metrics.select_all_cameras
        
        # Update UI
        context.area.tag_redraw()
        
        self.report({'INFO'}, f"Found {len(rc_metrics.cameras)} cameras with background images")
        return {'FINISHED'}

class RCMETRICS_OT_SelectAllCameras(bpy.types.Operator):
    """Select or deselect all cameras"""
    bl_idname = "rcmetrics.select_all_cameras"
    bl_label = "Select All Cameras"
    bl_options = {'REGISTER', 'UNDO'}
    
    select: BoolProperty(
        name="Select",
        description="Select or deselect all cameras",
        default=True
    )
    
    def execute(self, context):
        rc_metrics = context.scene.rc_metrics
        
        # Update the select_all_cameras property
        rc_metrics.select_all_cameras = self.select
        
        # Update all camera selections
        for camera in rc_metrics.cameras:
            camera.selected = self.select
        
        # Update UI
        context.area.tag_redraw()
        
        return {'FINISHED'}

class RCMETRICS_OT_ExportMetrics(bpy.types.Operator):
    """Export the calculated metrics to a JSON file"""
    bl_idname = "rcmetrics.export_metrics"
    bl_label = "Export Metrics"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        import json
        from datetime import datetime
        
        rc_metrics = context.scene.rc_metrics
        mesh_obj = context.active_object
        
        if not mesh_obj or mesh_obj.type != 'MESH':
            self.report({'ERROR'}, "No mesh object selected")
            return {'CANCELLED'}
        
        # Check if we have any results
        has_results = False
        for camera in rc_metrics.cameras:
            if camera.has_results:
                has_results = True
                break
        
        if not has_results:
            self.report({'ERROR'}, "No metric results available. Calculate metrics first.")
            return {'CANCELLED'}
        
        # Create output directory if needed
        metrics_output = rc_metrics.metrics_output
        if not metrics_output:
            # Create a default output folder
            rc_folder = rc_metrics.rc_folder
            metrics_output = os.path.join(rc_folder, "metrics_output")
        
        os.makedirs(metrics_output, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"metrics_{mesh_obj.name}_{timestamp}.json"
        filepath = os.path.join(metrics_output, filename)
        
        # Prepare data structure
        metrics_data = {
            "mesh_name": mesh_obj.name,
            "timestamp": timestamp,
            "cameras": [],
            "summary": {
                "average_psnr": rc_metrics.avg_psnr,
                "average_ssim": rc_metrics.avg_ssim,
                "min_psnr": rc_metrics.min_psnr,
                "min_ssim": rc_metrics.min_ssim,
                "max_psnr": rc_metrics.max_psnr,
                "max_ssim": rc_metrics.max_ssim
            }
        }
        
        # Add camera data
        for camera in rc_metrics.cameras:
            if camera.has_results:
                camera_data = {
                    "name": camera.name,
                    "psnr": camera.psnr,
                    "ssim": camera.ssim
                }
                metrics_data["cameras"].append(camera_data)
        
        # Write to file
        with open(filepath, 'w') as f:
            json.dump(metrics_data, f, indent=4)
        
        self.report({'INFO'}, f"Metrics exported to {filepath}")
        return {'FINISHED'}

# Register and unregister functions
def register():
    bpy.utils.register_class(RCMETRICS_OT_PopulateCameraList)
    bpy.utils.register_class(RCMETRICS_OT_SelectAllCameras)
    bpy.utils.register_class(RCMETRICS_OT_ExportMetrics)

def unregister():
    bpy.utils.unregister_class(RCMETRICS_OT_ExportMetrics)
    bpy.utils.unregister_class(RCMETRICS_OT_SelectAllCameras)
    bpy.utils.unregister_class(RCMETRICS_OT_PopulateCameraList)
