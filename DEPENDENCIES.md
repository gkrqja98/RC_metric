# How to Install Dependencies

This Blender add-on requires several Python packages to function correctly:
- numpy
- opencv-python (cv2)
- scikit-image

There are several ways to install these dependencies:

## Method 1: Using the Add-on's Install Button

1. Install the add-on in Blender
2. The add-on will detect missing dependencies
3. Click the "Install Dependencies" button that appears in the add-on panel
4. Restart Blender

## Method 2: Manual Installation with pip

If the automatic installation doesn't work, you can install the packages manually using pip:

1. Find your Blender's Python executable:
   - Windows: `C:\Program Files\Blender Foundation\Blender X.XX\X.XX\python\bin\python.exe`
   - macOS: `/Applications/Blender.app/Contents/Resources/X.XX/python/bin/python3.X`
   - Linux: `/usr/share/blender/X.XX/python/bin/python3.X`

2. Open a terminal or command prompt and run:
   ```
   "path/to/blender/python" -m pip install numpy opencv-python scikit-image
   ```

## Method 3: Using Blender's Python Console

1. Open Blender
2. Go to the Scripting workspace
3. In the Python Console, run:
   ```python
   import sys
   import subprocess
   subprocess.check_call([sys.executable, "-m", "pip", "install", "numpy", "opencv-python", "scikit-image"])
   ```

4. Restart Blender

## Troubleshooting

If you encounter issues with pip:

1. First try installing pip:
   ```python
   import subprocess
   import sys
   subprocess.check_call([sys.executable, "-m", "ensurepip"])
   ```

2. If you get permission errors, try running Blender as administrator/with sudo.

3. If you still have issues, consider creating a virtual environment and installing Blender's Python packages there.
