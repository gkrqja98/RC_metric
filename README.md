# RealityCapture Import Blender Add-on

A simple Blender add-on for importing RealityCapture results with proper setup.

## Features

- Automatically import RealityCapture .abc files
- Set camera resolutions and background images based on source images
- Apply textures to imported geometry with Emission shader
- Render from camera viewpoints and compare with original images
- Compute image quality metrics (PSNR, SSIM) between rendered and original images

## Installation

1. Download the latest release or clone this repository
2. In Blender, go to Edit > Preferences > Add-ons
3. Click "Install..." and select the downloaded .zip file or the `__init__.py` file
4. Enable the "RealityCapture Import" add-on

## Requirements

This add-on requires the following Python packages to be installed in Blender's bundled Python:
- numpy
- opencv-python (cv2)
- scikit-image (for image quality metrics)

See the DEPENDENCIES.md file for installation instructions.

## Usage

1. Navigate to the "RC Metrics" tab in the 3D View sidebar
2. Enter the path to your RealityCapture result folder (containing .abc file and images)
3. Click "Import RC & Setup"

### Image Comparison

1. Select a camera in the scene and make it active (Ctrl+0 or View > Cameras > Set Active)
2. Click the "Render and Compare" button (or press F12 to render)
3. View the PSNR and SSIM metrics comparing the rendered view with the original image

### Metrics Interpretation

- PSNR (Peak Signal-to-Noise Ratio): Higher values indicate better quality
  - > 30 dB: Good quality
  - > 40 dB: Excellent quality
- SSIM (Structural Similarity Index): Values range from 0 to 1
  - > 0.9: High similarity
  - > 0.95: Excellent match

## License

MIT
