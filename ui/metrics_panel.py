"""
Metrics panel UI for RC Metrics Add-on.
"""

import bpy
from bpy.types import Panel

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
            box.label(text="Results for Selected Camera:")
            
            # Find the camera with results
            for cam in rc_metrics.cameras:
                if cam.has_results:
                    box.label(text=f"Camera: {cam.name}")
                    
                    # Determine color based on thresholds
                    if cam.psnr < rc_metrics.psnr_threshold:
                        box.label(text=f"PSNR: {cam.psnr:.2f}", icon='ERROR')
                    else:
                        box.label(text=f"PSNR: {cam.psnr:.2f}", icon='CHECKMARK')
                        
                    if cam.ssim < rc_metrics.ssim_threshold:
                        box.label(text=f"SSIM: {cam.ssim:.4f}", icon='ERROR')
                    else:
                        box.label(text=f"SSIM: {cam.ssim:.4f}", icon='CHECKMARK')
                    break
            
            # Export buttons
            layout.operator("rcmetrics.export_results", text="Export Results", icon='FILE_TICK')

# Registration
def register():
    bpy.utils.register_class(RCMETRICS_PT_MetricsPanel)

def unregister():
    bpy.utils.unregister_class(RCMETRICS_PT_MetricsPanel)
