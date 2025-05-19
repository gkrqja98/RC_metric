import bpy
import importlib
import sys
import os

bl_info = {
    "name": "RealityCapture Metrics",
    "author": "Your Name",
    "version": (1, 0),
    "blender": (2, 93, 0),
    "location": "View3D > Sidebar > RC Metrics",
    "description": "Import RealityCapture results",
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
    # Register dependencies panel and operator (always registered)
    bpy.utils.register_class(RCMETRICS_OT_InstallDependencies)
    bpy.utils.register_class(RCMETRICS_PT_DependenciesPanel)
    
    # Register properties
    from . import properties
    properties.register()
    
    # Register operators
    from .operators import import_operators, render_operators
    import_operators.register()
    render_operators.register()
    
    # Register UI components
    from .ui import main_panel
    main_panel.register()

def unregister():
    # Try to unregister dependencies panel
    try:
        bpy.utils.unregister_class(RCMETRICS_PT_DependenciesPanel)
        bpy.utils.unregister_class(RCMETRICS_OT_InstallDependencies)
    except:
        pass
    
    # Try to unregister UI components
    try:
        from .ui import main_panel
        main_panel.unregister()
    except:
        pass
    
    # Try to unregister operators
    try:
        from .operators import import_operators, render_operators
        render_operators.unregister()
        import_operators.unregister()
    except:
        pass
    
    # Try to unregister properties
    try:
        from . import properties
        properties.unregister()
    except:
        pass

if __name__ == "__main__":
    register()
