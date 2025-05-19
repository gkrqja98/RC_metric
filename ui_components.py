"""
UI components for the RC Metrics add-on.
"""

import bpy
from bpy.types import Panel, Operator
from bpy.props import BoolProperty, EnumProperty, FloatProperty

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
        
        row = layout.row()
        row.operator("rcmetrics.select_all_cameras", text="Select All")
        row.operator("rcmetrics.deselect_all_cameras", text="Deselect All")
        
        # Show the camera list
        row = layout.row()
        row.template_list("RCMETRICS_UL_CamerasList", "", rc_metrics, "cameras", 
                         rc_metrics, "active_camera_index", rows=5)
        
        # Show stats
        if len(rc_metrics.cameras) > 0:
            layout.label(text=f"Total: {len(rc_metrics.cameras)} cameras")
            
            # Count enabled cameras
            enabled_count = sum(1 for cam in rc_metrics.cameras if cam.enabled)
            layout.label(text=f"Enabled: {enabled_count} cameras")
            
            # Count cameras with results
            results_count = sum(1 for cam in rc_metrics.cameras if cam.has_results)
            if results_count > 0:
                layout.label(text=f"Calculated: {results_count}/{enabled_count}")
                
                # If we have results, show averages
                problematic_count = sum(1 for cam in rc_metrics.cameras if cam.has_results and cam.is_problematic)
                if problematic_count > 0:
                    layout.label(text=f"Problematic: {problematic_count}", icon='ERROR')
        
        # Add refresh UI button
        layout.operator("rcmetrics.refresh_ui", text="Refresh UI", icon='FILE_REFRESH')

class RCMETRICS_PT_MetricsPanel(Panel):
    """Metrics Calculation Panel"""
    bl_label = "Metrics Settings"
    bl_idname = "RCMETRICS_PT_MetricsPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'RC Metrics'
    bl_parent_id = "RCMETRICS_PT_Panel"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        rc_metrics = context.scene.rc_metrics
        
        # Render and save options
        box = layout.box()
        box.label(text="Render Options:")
        box.prop(rc_metrics, "save_renders")
        box.prop(rc_metrics, "render_quality")
        
        # Threshold settings
        box = layout.box()
        box.label(text="Threshold Settings:")
        box.prop(rc_metrics, "psnr_threshold")
        box.prop(rc_metrics, "ssim_threshold")
        
        # Current status display
        if rc_metrics.is_calculating:
            layout.label(text="Calculation in progress...", icon='SORTTIME')
            layout.label(text=f"Processing: {rc_metrics.current_camera}")
            layout.label(text=f"Progress: {rc_metrics.calculation_progress}%")
            
            # Progress bar (using a fancy box fill)
            box = layout.box()
            row = box.row()
            progress_blocks = int(rc_metrics.calculation_progress / 5)  # 20 blocks for 100%
            for i in range(20):
                if i < progress_blocks:
                    row.label(text="█")
                else:
                    row.label(text="░")
            
            # Cancel button
            layout.operator("rcmetrics.cancel_calculation", text="Cancel", icon='X')
        
        # Results summary if available
        if rc_metrics.has_results and not rc_metrics.is_calculating:
            box = layout.box()
            box.label(text="Results Summary:")
            box.label(text=f"Average PSNR: {rc_metrics.average_psnr:.2f}")
            box.label(text=f"Average SSIM: {rc_metrics.average_ssim:.4f}")
            
            # Export button
            layout.operator("rcmetrics.export_results", text="Export Results", icon='FILE_TICK')

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

class RCMETRICS_OT_RefreshCameras(Operator):
    """Refresh the camera list"""
    bl_idname = "rcmetrics.refresh_cameras"
    bl_label = "Refresh Cameras"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        from . import camera_utils
        count = camera_utils.update_camera_list(context)
        self.report({'INFO'}, f"Found {count} cameras")
        return {'FINISHED'}

class RCMETRICS_OT_SelectAllCameras(Operator):
    """Select all cameras in the list"""
    bl_idname = "rcmetrics.select_all_cameras"
    bl_label = "Select All Cameras"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        from . import camera_utils
        count = camera_utils.select_all_cameras(context, True)
        self.report({'INFO'}, f"Selected {count} cameras")
        return {'FINISHED'}

class RCMETRICS_OT_DeselectAllCameras(Operator):
    """Deselect all cameras in the list"""
    bl_idname = "rcmetrics.deselect_all_cameras"
    bl_label = "Deselect All Cameras"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        from . import camera_utils
        count = camera_utils.select_all_cameras(context, False)
        self.report({'INFO'}, f"Deselected {count} cameras")
        return {'FINISHED'}

class RCMETRICS_OT_CancelCalculation(Operator):
    """Cancel the current metrics calculation"""
    bl_idname = "rcmetrics.cancel_calculation"
    bl_label = "Cancel Calculation"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        rc_metrics = context.scene.rc_metrics
        rc_metrics.is_calculating = False
        self.report({'INFO'}, "Calculation cancelled")
        return {'FINISHED'}

class RCMETRICS_OT_ExportResults(Operator):
    """Export metrics results to a JSON file"""
    bl_idname = "rcmetrics.export_results"
    bl_label = "Export Results"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        import json
        import os
        
        rc_metrics = context.scene.rc_metrics
        
        # Create results dictionary
        results = {
            "mesh_name": context.active_object.name if context.active_object else "Unknown",
            "average_psnr": rc_metrics.average_psnr,
            "average_ssim": rc_metrics.average_ssim,
            "min_psnr": min([cam.psnr for cam in rc_metrics.cameras if cam.has_results], default=0),
            "min_ssim": min([cam.ssim for cam in rc_metrics.cameras if cam.has_results], default=0),
            "max_psnr": max([cam.psnr for cam in rc_metrics.cameras if cam.has_results], default=0),
            "max_ssim": max([cam.ssim for cam in rc_metrics.cameras if cam.has_results], default=0),
            "cameras": []
        }
        
        # Add camera data
        for cam in rc_metrics.cameras:
            if cam.has_results:
                results["cameras"].append({
                    "camera": cam.name,
                    "psnr": cam.psnr,
                    "ssim": cam.ssim,
                    "is_problematic": cam.is_problematic
                })
        
        # Save to file
        output_dir = rc_metrics.metrics_output
        if not output_dir:
            output_dir = os.path.join(rc_metrics.rc_folder, "metrics_output")
            os.makedirs(output_dir, exist_ok=True)
            
        filepath = os.path.join(output_dir, f"metrics_{context.active_object.name if context.active_object else 'unknown'}.json")
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=4)
            
        self.report({'INFO'}, f"Results exported to {filepath}")
        return {'FINISHED'}

# Register all classes
def register_ui():
    bpy.utils.register_class(RCMETRICS_PT_CameraPanel)
    bpy.utils.register_class(RCMETRICS_PT_MetricsPanel)
    bpy.utils.register_class(RCMETRICS_OT_RefreshUI)
    bpy.utils.register_class(RCMETRICS_OT_RefreshCameras)
    bpy.utils.register_class(RCMETRICS_OT_SelectAllCameras)
    bpy.utils.register_class(RCMETRICS_OT_DeselectAllCameras)
    bpy.utils.register_class(RCMETRICS_OT_CancelCalculation)
    bpy.utils.register_class(RCMETRICS_OT_ExportResults)
    
def unregister_ui():
    bpy.utils.unregister_class(RCMETRICS_OT_ExportResults)
    bpy.utils.unregister_class(RCMETRICS_OT_CancelCalculation)
    bpy.utils.unregister_class(RCMETRICS_OT_DeselectAllCameras)
    bpy.utils.unregister_class(RCMETRICS_OT_SelectAllCameras)
    bpy.utils.unregister_class(RCMETRICS_OT_RefreshCameras)
    bpy.utils.unregister_class(RCMETRICS_OT_RefreshUI)
    bpy.utils.unregister_class(RCMETRICS_PT_MetricsPanel)
    bpy.utils.unregister_class(RCMETRICS_PT_CameraPanel)
