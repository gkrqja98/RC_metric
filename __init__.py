import bpy
import importlib
import sys
import os

bl_info = {
    "name": "RealityCapture Metrics",
    "author": "Your Name",
    "version": (1, 1),
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

# Module reload mechanism for development
def reload_modules():
    """Reload all addon modules - for development"""
    # List all modules to reload
    modules = [
        "properties",
        "operators",
        "operators.import_operators",
        "operators.camera_operators",
        "operators.metrics_operators",
        "operators.export_operators",
        "utils",
        "utils.camera_utils",
        "utils.render_utils",
        "utils.image_utils",
        "utils.file_utils",
        "ui",
        "ui.main_panel",
        "ui.camera_panel",
        "ui.metrics_panel"
    ]
    
    # Reload modules
    for module_name in modules:
        full_module_name = f"rc_metric.{module_name}"
        if full_module_name in sys.modules:
            importlib.reload(sys.modules[full_module_name])

# Registration
def register():
    try:
        # Try to import the required modules
        import numpy
        import cv2
        import skimage.metrics
        
        # Reload modules if needed (for development)
        reload_modules()
        
        # Register dependencies panel and operator (always registered)
        bpy.utils.register_class(RCMETRICS_OT_InstallDependencies)
        bpy.utils.register_class(RCMETRICS_PT_DependenciesPanel)
        
        # Register properties
        from . import properties
        properties.register()
        
        # Register operators
        from .operators import import_operators
        from .operators import camera_operators
        from .operators import metrics_operators
        from .operators import export_operators
        
        import_operators.register()
        camera_operators.register()
        metrics_operators.register()
        export_operators.register()
        
        # Register UI components
        from .ui import main_panel
        from .ui import camera_panel
        from .ui import metrics_panel
        
        main_panel.register()
        camera_panel.register()
        metrics_panel.register()
        
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
        
        # Try to unregister UI components
        try:
            from .ui import main_panel
            from .ui import camera_panel
            from .ui import metrics_panel
            
            metrics_panel.unregister()
            camera_panel.unregister()
            main_panel.unregister()
        except:
            pass
        
        # Try to unregister operators
        try:
            from .operators import import_operators
            from .operators import camera_operators
            from .operators import metrics_operators
            from .operators import export_operators
            
            export_operators.unregister()
            metrics_operators.unregister()
            camera_operators.unregister()
            import_operators.unregister()
        except:
            pass
        
        # Try to unregister properties
        try:
            from . import properties
            properties.unregister()
        except:
            pass
            
    except:
        pass

if __name__ == "__main__":
    register()
