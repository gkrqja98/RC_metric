# Dependencies for RC Import Add-on

This add-on requires the following Python packages to be installed in Blender's Python environment:

- `numpy`
- `opencv-python` (cv2)
- `scikit-image` (for image quality metrics)

## Installation Steps

### Method 1: Using Blender's Python

1. Locate Blender's Python executable. For example:
   - Windows: `C:\Program Files\Blender Foundation\Blender 4.2\4.2\python\bin\python.exe`
   - macOS: `/Applications/Blender.app/Contents/Resources/4.2/python/bin/python3.11`
   - Linux: `/usr/share/blender/4.2/python/bin/python3.11`

2. Open a terminal/command prompt and run:
   ```
   "[Blender Python Path]" -m pip install numpy opencv-python scikit-image
   ```

### Method 2: Using Blender's Console

1. Open Blender
2. Go to the Python Console in Blender
3. Run the following commands:
   ```python
   import sys
   import subprocess
   subprocess.check_call([sys.executable, "-m", "pip", "install", "numpy", "opencv-python", "scikit-image"])
   ```

### Troubleshooting

If you encounter issues:

1. Make sure you're using the correct Python version that matches Blender's Python
2. On some systems, you may need administrator/root privileges
3. If you get SSL errors, try adding the `--trusted-host pypi.org --trusted-host files.pythonhosted.org` flags to pip
