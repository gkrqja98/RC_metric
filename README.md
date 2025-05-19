# RealityCapture Import Blender Add-on

A simple Blender add-on for importing RealityCapture results with proper setup.

## Features

- Automatically import RealityCapture .abc files
- Set camera resolutions and background images based on source images
- Apply textures to imported geometry with Emission shader

## Installation

1. Download the latest release or clone this repository
2. In Blender, go to Edit > Preferences > Add-ons
3. Click "Install..." and select the downloaded .zip file or the `__init__.py` file
4. Enable the "RealityCapture Import" add-on

## Requirements

This add-on requires the following Python packages to be installed in Blender's bundled Python:
- numpy
- opencv-python (cv2)

See the DEPENDENCIES.md file for installation instructions.

## Usage

1. Navigate to the "RC Import" tab in the 3D View sidebar
2. Enter the path to your RealityCapture result folder (containing .abc file and images)
3. Click "Import RC & Setup"

## License

MIT
