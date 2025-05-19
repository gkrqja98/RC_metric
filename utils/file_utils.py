"""
File utilities for the RC Metrics add-on.
This module handles file operations and validations.
"""

import os
import json
import bpy

def ensure_directory_exists(directory_path):
    """Ensure a directory exists, creating it if needed"""
    if not os.path.exists(directory_path):
        try:
            os.makedirs(directory_path, exist_ok=True)
            return True
        except Exception as e:
            print(f"Error creating directory {directory_path}: {e}")
            return False
    return True

def save_json(data, filepath):
    """Save data as JSON to a file"""
    try:
        directory = os.path.dirname(filepath)
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving JSON to {filepath}: {e}")
        return False

def load_json(filepath):
    """Load JSON data from a file"""
    try:
        if not os.path.exists(filepath):
            print(f"File does not exist: {filepath}")
            return None
            
        with open(filepath, 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Error loading JSON from {filepath}: {e}")
        return None

def get_default_output_path(rc_folder, subfolder=None):
    """Get a default output path based on the RC folder"""
    if not rc_folder:
        # Use the .blend file location as fallback
        blend_path = bpy.path.abspath("//")
        if blend_path:
            output_path = os.path.join(blend_path, "metrics_output")
        else:
            # Last resort: use temp directory
            import tempfile
            output_path = os.path.join(tempfile.gettempdir(), "blender_rc_metrics")
    else:
        output_path = os.path.join(rc_folder, "metrics_output")
    
    # Add subfolder if specified
    if subfolder:
        output_path = os.path.join(output_path, subfolder)
    
    # Ensure the directory exists
    ensure_directory_exists(output_path)
    
    return output_path

def get_valid_filepath(directory, filename, extension):
    """Get a valid filepath, avoiding overwriting existing files"""
    base_path = os.path.join(directory, filename)
    filepath = f"{base_path}.{extension}"
    
    # If file exists, add a number
    counter = 1
    while os.path.exists(filepath):
        filepath = f"{base_path}_{counter}.{extension}"
        counter += 1
    
    return filepath

def find_file_by_extension(directory, extension):
    """Find files with specific extension in a directory"""
    if not os.path.exists(directory):
        return []
        
    return [f for f in os.listdir(directory) if f.endswith(f".{extension}")]
