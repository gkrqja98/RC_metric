# RealityCapture Metrics Blender Add-on

A Blender add-on for importing RealityCapture results and calculating image-based metrics between 3D models.

## Features

- Automatically import RealityCapture .abc files with proper setup
- Set camera resolutions and background images based on source images
- Apply textures to imported geometry
- Render selected meshes from all camera positions
- Calculate PSNR and SSIM metrics between renders and original images
- Export metrics as JSON reports

## Installation

1. Download the latest release or clone this repository
2. In Blender, go to Edit > Preferences > Add-ons
3. Click "Install..." and select the downloaded .zip file or the `__init__.py` file
4. Enable the "RealityCapture Metrics" add-on

## Requirements

This add-on requires the following Python packages to be installed in Blender's bundled Python:
- numpy
- opencv-python (cv2)
- scikit-image

## Usage

### 1. Import RealityCapture Results

1. Navigate to the "RC Metrics" tab in the 3D View sidebar
2. Enter the path to your RealityCapture result folder (containing .abc file and images)
3. Click "1. Import RC & Setup"

### 2. Calculate Metrics

1. Select the mesh you want to evaluate (click it in the Scene Collection)
2. Optionally specify an output folder for metrics results
3. Click "2. Calculate Metrics"

## Understanding the Metrics

- **PSNR (Peak Signal-to-Noise Ratio)**: Measures the quality difference between two images. Higher values indicate more similar images.
- **SSIM (Structural Similarity Index)**: An image similarity measure based on human visual perception. Values closer to 1 indicate greater similarity.

## License

MIT

## Citation

If you use this tool in your research, please cite it as:

```
@software{rcmetrics,
  author = {Your Name},
  title = {RealityCapture Metrics},
  url = {https://github.com/yourusername/rc_metric},
  year = {2025},
}
```
