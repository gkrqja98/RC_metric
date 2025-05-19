import bpy
from . import rc_metrics

bl_info = {
    "name": "RealityCapture Metrics",
    "author": "Your Name",
    "version": (1, 0),
    "blender": (2, 93, 0),
    "location": "View3D > Sidebar > RC Metrics",
    "description": "Import RealityCapture results and calculate metrics",
    "warning": "Requires additional Python packages",
    "doc_url": "https://github.com/yourusername/rc_metric",
    "category": "3D View",
}

# Required packages
required_packages = ["numpy", "opencv-python", "scikit-image"]

def check_dependencies():
    """Check if all required packages are installed"""
    missing_packages = []
    
    for package in required_packages:
        package_name = package.split('[')[0]  # Remove any extras
        try:
            __import__(package_name)
        except ImportError:
            missing_packages.append(package)
    
    return missing_packages

class RCMETRICS_OT_InstallDependencies(bpy.types.Operator):
    """Install required Python dependencies"""
    bl_idname = "rcmetrics.install_dependencies"
    bl_label = "Install Dependencies"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        self.report({'INFO'}, "Please see DEPENDENCIES.md for installation instructions")
        return {'FINISHED'}

class RCMETRICS_PT_DependenciesPanel(bpy.types.Panel):
    """Dependencies Panel"""
    bl_label = "Dependencies"
    bl_idname = "RCMETRICS_PT_DependenciesPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'RC Metrics'
    
    def draw(self, context):
        layout = self.layout
        
        missing_packages = check_dependencies()
        
        if missing_packages:
            layout.label(text="Missing required packages:", icon='ERROR')
            for package in missing_packages:
                layout.label(text=f"- {package}")
            layout.operator("rcmetrics.install_dependencies")
            layout.label(text="See DEPENDENCIES.md for instructions")
        else:
            layout.label(text="All dependencies installed", icon='CHECKMARK')

# Registration
def register():
    try:
        # Try to import the required modules
        import numpy
        import cv2
        import skimage.metrics
        
        # Register the main add-on
        bpy.utils.register_class(rc_metrics.RCMetricsProperties)
        bpy.utils.register_class(rc_metrics.RCMETRICS_OT_ImportRC)
        bpy.utils.register_class(rc_metrics.RCMETRICS_OT_CalculateMetrics)
        bpy.utils.register_class(rc_metrics.RCMETRICS_PT_Panel)
        bpy.types.Scene.rc_metrics = bpy.props.PointerProperty(type=rc_metrics.RCMetricsProperties)
        
    except ImportError as e:
        # If missing dependencies, only register the dependencies panel
        print(f"Error loading RC Metrics add-on: {e}")
        print("Please install the required dependencies")
        
        bpy.utils.register_class(RCMETRICS_OT_InstallDependencies)
        bpy.utils.register_class(RCMETRICS_PT_DependenciesPanel)

def unregister():
    try:
        # Try to unregister dependencies panel
        try:
            bpy.utils.unregister_class(RCMETRICS_PT_DependenciesPanel)
            bpy.utils.unregister_class(RCMETRICS_OT_InstallDependencies)
        except:
            pass
        
        # Try to unregister main add-on
        try:
            bpy.utils.unregister_class(rc_metrics.RCMETRICS_PT_Panel)
            bpy.utils.unregister_class(rc_metrics.RCMETRICS_OT_CalculateMetrics)
            bpy.utils.unregister_class(rc_metrics.RCMETRICS_OT_ImportRC)
            bpy.utils.unregister_class(rc_metrics.RCMetricsProperties)
            del bpy.types.Scene.rc_metrics
        except:
            pass
    except:
        pass

if __name__ == "__main__":
    register()
