"""
Export operators for RC Metrics Add-on.
This module handles exporting metrics results.
"""

import bpy
import os
import json
from bpy.props import StringProperty
from datetime import datetime

class RCMETRICS_OT_ExportResults(bpy.types.Operator):
    """Export metrics results to a JSON file"""
    bl_idname = "rcmetrics.export_results"
    bl_label = "Export Results"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
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

class RCMETRICS_OT_ExportMetricsReport(bpy.types.Operator):
    """Export a more detailed metrics report as HTML"""
    bl_idname = "rcmetrics.export_report"
    bl_label = "Export HTML Report"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        rc_metrics = context.scene.rc_metrics
        
        # Check if we have results to export
        if not rc_metrics.has_results:
            self.report({'ERROR'}, "No metrics results available. Calculate metrics first.")
            return {'CANCELLED'}
        
        # Create report output directory
        output_dir = rc_metrics.metrics_output
        if not output_dir:
            output_dir = os.path.join(rc_metrics.rc_folder, "metrics_output")
            
        report_dir = os.path.join(output_dir, "report")
        os.makedirs(report_dir, exist_ok=True)
        
        # Create the HTML report
        html_report = self.generate_html_report(context, report_dir)
        
        # Save the report
        report_path = os.path.join(report_dir, "metrics_report.html")
        with open(report_path, 'w') as f:
            f.write(html_report)
            
        self.report({'INFO'}, f"HTML report exported to {report_path}")
        return {'FINISHED'}
    
    def generate_html_report(self, context, report_dir):
        """Generate HTML report from metrics results"""
        rc_metrics = context.scene.rc_metrics
        
        # Basic HTML template
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>RC Metrics Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1, h2 { color: #333; }
                .summary { background-color: #f5f5f5; padding: 15px; border-radius: 5px; }
                .camera-item { margin-bottom: 10px; padding: 10px; border: 1px solid #ddd; }
                .problematic { background-color: #ffeeee; }
                .good { background-color: #eeffee; }
                .metrics { font-weight: bold; }
                .psnr-low { color: red; }
                .ssim-low { color: red; }
                .psnr-good { color: green; }
                .ssim-good { color: green; }
                table { border-collapse: collapse; width: 100%; margin-top: 20px; }
                th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
                th { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <h1>RealityCapture Metrics Report</h1>
        """
        
        # Add summary section
        html += """
            <div class="summary">
                <h2>Summary</h2>
                <p><strong>Model:</strong> {}</p>
                <p><strong>Average PSNR:</strong> {:.2f}</p>
                <p><strong>Average SSIM:</strong> {:.4f}</p>
                <p><strong>Generated:</strong> {}</p>
            </div>
        """.format(
            context.active_object.name if context.active_object else "Unknown",
            rc_metrics.average_psnr,
            rc_metrics.average_ssim,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        # Add camera results table
        html += """
            <h2>Camera Results</h2>
            <table>
                <tr>
                    <th>Camera</th>
                    <th>PSNR</th>
                    <th>SSIM</th>
                    <th>Status</th>
                </tr>
        """
        
        # Add each camera's results
        for cam in rc_metrics.cameras:
            if cam.has_results:
                # Determine CSS classes for styling
                psnr_class = "psnr-low" if cam.psnr < rc_metrics.psnr_threshold else "psnr-good"
                ssim_class = "ssim-low" if cam.ssim < rc_metrics.ssim_threshold else "ssim-good"
                row_class = "problematic" if cam.is_problematic else "good"
                status = "Problem" if cam.is_problematic else "Good"
                
                html += """
                    <tr class="{}">
                        <td>{}</td>
                        <td class="{}">{:.2f}</td>
                        <td class="{}">{:.4f}</td>
                        <td>{}</td>
                    </tr>
                """.format(
                    row_class,
                    cam.name,
                    psnr_class, cam.psnr,
                    ssim_class, cam.ssim,
                    status
                )
        
        # Close the table and HTML
        html += """
            </table>
        </body>
        </html>
        """
        
        return html

# Registration
def register():
    bpy.utils.register_class(RCMETRICS_OT_ExportResults)
    bpy.utils.register_class(RCMETRICS_OT_ExportMetricsReport)

def unregister():
    bpy.utils.unregister_class(RCMETRICS_OT_ExportMetricsReport)
    bpy.utils.unregister_class(RCMETRICS_OT_ExportResults)
