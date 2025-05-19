"""
Metrics calculation operators for RC Metrics Add-on.
This module handles metrics calculation between images.
"""

import bpy
import os
import json
import time

class RCMETRICS_OT_CalculateMetrics(bpy.types.Operator):
    """Render current mesh from selected cameras and calculate metrics"""
    bl_idname = "rcmetrics.calculate_metrics"
    bl_label = "2. Calculate Metrics"
    bl_options = {'REGISTER', 'UNDO'}
    
    _timer = None
    _camera_queue = []
    _metrics_summary = {}
    
    def modal(self, context, event):
        """Modal function for handling the metrics calculation"""
        rc_metrics = context.scene.rc_metrics
        
        # Check if calculation should be cancelled
        if not rc_metrics.is_calculating:
            self.cancel(context)
            return {'CANCELLED'}
            
        # Process timer events
        if event.type == 'TIMER':
            # If we have cameras to process
            if self._camera_queue:
                # Get the next camera
                camera = self._camera_queue.pop(0)
                rc_metrics.current_camera = camera.name
                
                # Update progress
                progress = 100.0 * (1.0 - len(self._camera_queue) / self._total_cameras)
                rc_metrics.calculation_progress = progress
                
                # Process this camera
                self.process_camera(context, camera)
                
                # Force UI update
                for area in context.screen.areas:
                    area.tag_redraw()
                
                # We're still processing, continue modal
                return {'RUNNING_MODAL'}
            else:
                # We're done, finalize and finish
                self.finish_calculation(context)
                
                # Force UI update once more before finishing
                for area in context.screen.areas:
                    area.tag_redraw()
                
                return {'FINISHED'}
                
        # Continue running modal
        return {'RUNNING_MODAL'}
    
    def invoke(self, context, event):
        """Start the modal timer"""
        # Import required modules
        from ..utils import camera_utils
        from ..utils import render_utils
        
        # Check active object
        if not context.active_object or context.active_object.type != 'MESH':
            self.report({'ERROR'}, "Please select a mesh object to evaluate")
            return {'CANCELLED'}
            
        # Get folder paths
        rc_metrics = context.scene.rc_metrics
        
        if not rc_metrics.metrics_output and rc_metrics.save_renders:
            # Create a default output folder if not specified
            rc_metrics.metrics_output = os.path.join(rc_metrics.rc_folder, "metrics_output")
            try:
                os.makedirs(rc_metrics.metrics_output, exist_ok=True)
            except:
                self.report({'ERROR'}, f"Could not create output directory: {rc_metrics.metrics_output}")
                return {'CANCELLED'}
        
        # Get enabled cameras
        self._camera_queue = camera_utils.get_enabled_cameras(context)
        
        if not self._camera_queue:
            self.report({'ERROR'}, "No cameras selected for calculation")
            return {'CANCELLED'}
            
        # Initialize calculation
        self._total_cameras = len(self._camera_queue)
        self._metrics_summary = {
            "mesh_name": context.active_object.name,
            "cameras": [],
            "average_psnr": 0.0,
            "average_ssim": 0.0,
            "min_psnr": float('inf'),
            "min_ssim": float('inf'),
            "max_psnr": 0.0,
            "max_ssim": 0.0
        }
        
        # Setup render settings
        render_utils.setup_render_settings(context, rc_metrics.render_quality)
        
        # Create render output if saving renders
        if rc_metrics.save_renders:
            self._render_output = os.path.join(rc_metrics.metrics_output, "renders")
            try:
                os.makedirs(self._render_output, exist_ok=True)
            except:
                self.report({'ERROR'}, f"Could not create render output directory: {self._render_output}")
                return {'CANCELLED'}
        else:
            self._render_output = None
        
        # Start modal timer
        # Increase timer interval to 2.0 seconds to give more time for UI updates
        self._timer = context.window_manager.event_timer_add(2.0, window=context.window)
        context.window_manager.modal_handler_add(self)
        
        # Set calculation in progress
        rc_metrics.is_calculating = True
        rc_metrics.calculation_progress = 0.0
        rc_metrics.has_results = False
        
        self.report({'INFO'}, f"Starting calculation for {self._total_cameras} cameras")
        return {'RUNNING_MODAL'}
    
    def process_camera(self, context, camera):
        """Process a single camera"""
        from ..utils import camera_utils
        from ..utils import render_utils
        
        rc_metrics = context.scene.rc_metrics
        
        # Render from this camera
        if rc_metrics.save_renders:
            render_img_path = os.path.join(self._render_output, f"{camera.name.split('.')[0]}_render.png")
            self.report({'INFO'}, f"Rendering from camera: {camera.name}")
            rendered_img = render_utils.render_from_camera(context, camera, render_img_path)
        else:
            self.report({'INFO'}, f"Processing camera: {camera.name}")
            rendered_img = render_utils.render_from_camera(context, camera, None)
        
        # Get the reference image
        ref_img = render_utils.get_camera_background_image(camera)
        
        # Calculate metrics
        if ref_img is not None and rendered_img is not None:
            psnr, ssim = render_utils.calculate_image_metrics(ref_img, rendered_img)
            
            if psnr is not None and ssim is not None:
                # Update metrics summary
                self._metrics_summary = render_utils.update_metrics_summary(
                    self._metrics_summary, camera.name, psnr, ssim)
                
                # Update UI list
                result = camera_utils.update_camera_results(context, camera.name, psnr, ssim, 
                                                  rc_metrics.psnr_threshold, rc_metrics.ssim_threshold)
                
                # Debug info
                if not result:
                    self.report({'WARNING'}, f"Failed to update UI for camera: {camera.name}")
                
                # Report results
                self.report({'INFO'}, f"Camera: {camera.name}, PSNR: {psnr:.2f}, SSIM: {ssim:.4f}")
                
                # Update averages in the UI
                rc_metrics.average_psnr = self._metrics_summary["average_psnr"]
                rc_metrics.average_ssim = self._metrics_summary["average_ssim"]
                rc_metrics.has_results = True
                
                return True
            
        self.report({'WARNING'}, f"Could not calculate metrics for camera: {camera.name}")
        return False
    
    def finish_calculation(self, context):
        """Finish the calculation and clean up"""
        rc_metrics = context.scene.rc_metrics
        
        # Save metrics to file if we have results and are saving renders
        if rc_metrics.has_results and rc_metrics.save_renders:
            metrics_file = os.path.join(rc_metrics.metrics_output, 
                                        f"metrics_{self._metrics_summary['mesh_name']}.json")
            with open(metrics_file, 'w') as f:
                json.dump(self._metrics_summary, f, indent=4)
                
            self.report({'INFO'}, f"Metrics saved to: {metrics_file}")
        
        # Clean up
        rc_metrics.is_calculating = False
        rc_metrics.calculation_progress = 100.0
        rc_metrics.current_camera = ""
        
        camera_count = len(self._metrics_summary.get("cameras", []))
        self.report({'INFO'}, f"Calculation completed for {camera_count} cameras")
        self.report({'INFO'}, f"Average PSNR: {rc_metrics.average_psnr:.2f}, Average SSIM: {rc_metrics.average_ssim:.4f}")
        
        # Show results for cameras where update_camera_results failed
        for cam_info in self._metrics_summary.get("cameras", []):
            camera_name = cam_info["camera"]
            psnr = cam_info["psnr"]
            ssim = cam_info["ssim"]
            print(f"Results for {camera_name}: PSNR={psnr:.2f}, SSIM={ssim:.4f}")
        
        # Force a final UI update
        for area in context.screen.areas:
            area.tag_redraw()
    
    def cancel(self, context):
        """Cancel the calculation"""
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None
            
        # Clean up
        context.scene.rc_metrics.is_calculating = False
        context.scene.rc_metrics.current_camera = ""
        
        self.report({'INFO'}, "Calculation cancelled")

class RCMETRICS_OT_CancelCalculation(bpy.types.Operator):
    """Cancel the current metrics calculation"""
    bl_idname = "rcmetrics.cancel_calculation"
    bl_label = "Cancel Calculation"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        rc_metrics = context.scene.rc_metrics
        rc_metrics.is_calculating = False
        self.report({'INFO'}, "Calculation cancelled")
        return {'FINISHED'}

# Registration
def register():
    bpy.utils.register_class(RCMETRICS_OT_CalculateMetrics)
    bpy.utils.register_class(RCMETRICS_OT_CancelCalculation)

def unregister():
    bpy.utils.unregister_class(RCMETRICS_OT_CancelCalculation)
    bpy.utils.unregister_class(RCMETRICS_OT_CalculateMetrics)
