import bpy
from bpy.props import BoolProperty, FloatProperty, StringProperty, PointerProperty, CollectionProperty
from bpy.types import PropertyGroup

class CameraItemProperties(PropertyGroup):
    """Properties for each camera item in the list"""
    selected: BoolProperty(
        name="Select",
        description="Select this camera for metric calculation",
        default=True
    )
    
    name: StringProperty(
        name="Name",
        description="Camera name",
        default=""
    )
    
    psnr: FloatProperty(
        name="PSNR",
        description="Peak Signal-to-Noise Ratio",
        default=0.0,
        precision=2
    )
    
    ssim: FloatProperty(
        name="SSIM",
        description="Structural Similarity Index",
        default=0.0,
        precision=4
    )
    
    camera: PointerProperty(
        type=bpy.types.Object
    )
    
    has_results: BoolProperty(
        name="Has Results",
        description="Whether this camera has metric results",
        default=False
    )

class RCMetricsProperties(PropertyGroup):
    """Property group for RC Metrics add-on"""
    rc_folder: StringProperty(
        name="RC Result Folder",
        description="Path to the RealityCapture result folder",
        default="",
        subtype='DIR_PATH'
    )
    
    metrics_output: StringProperty(
        name="Metrics Output",
        description="Path to save the metrics results",
        default="",
        subtype='DIR_PATH'
    )
    
    save_renders: BoolProperty(
        name="Save Rendered Images",
        description="Save rendered images to disk",
        default=True
    )
    
    calculate_metrics_only: BoolProperty(
        name="Calculate Metrics Only",
        description="Calculate metrics without saving renders",
        default=False
    )
    
    psnr_threshold: FloatProperty(
        name="PSNR Threshold",
        description="Threshold for highlighting low PSNR values",
        default=30.0,
        min=0.0,
        max=100.0
    )
    
    ssim_threshold: FloatProperty(
        name="SSIM Threshold",
        description="Threshold for highlighting low SSIM values",
        default=0.9,
        min=0.0,
        max=1.0,
        precision=3
    )
    
    select_all_cameras: BoolProperty(
        name="Select All",
        description="Select all cameras",
        default=True
    )
    
    # Collection of camera items
    cameras: CollectionProperty(
        type=CameraItemProperties
    )
    
    # Index of the active camera item
    active_camera_index: bpy.props.IntProperty()
    
    # Summary statistics
    avg_psnr: FloatProperty(
        name="Average PSNR",
        default=0.0,
        precision=2
    )
    
    avg_ssim: FloatProperty(
        name="Average SSIM",
        default=0.0,
        precision=4
    )
    
    min_psnr: FloatProperty(
        name="Min PSNR",
        default=0.0,
        precision=2
    )
    
    min_ssim: FloatProperty(
        name="Min SSIM",
        default=0.0,
        precision=4
    )
    
    max_psnr: FloatProperty(
        name="Max PSNR",
        default=0.0,
        precision=2
    )
    
    max_ssim: FloatProperty(
        name="Max SSIM",
        default=0.0,
        precision=4
    )
    
    # Status
    processing_camera: StringProperty(
        name="Processing Camera",
        default=""
    )
    
    is_processing: BoolProperty(
        name="Is Processing",
        default=False
    )
    
    # Register the classes
    def register():
        bpy.utils.register_class(CameraItemProperties)
        bpy.utils.register_class(RCMetricsProperties)
    
    # Unregister the classes
    def unregister():
        bpy.utils.unregister_class(RCMetricsProperties)
        bpy.utils.unregister_class(CameraItemProperties)
