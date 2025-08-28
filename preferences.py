import bpy
import platform
import requests
import zipfile
import threading
import os
from pathlib import Path
import importlib
import subprocess
import sys

# --- Dependency Management ---

optional_dependencies = [
    "laspy",
    "pylas",
    "imageio",
    "plyfile",
]

def is_module_installed(module_name):
    """Checks if a Python module is installed."""
    try:
        importlib.invalidate_caches()
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False

def run_pip(args):
    """Runs a pip command and waits for it to complete."""
    try:
        subprocess.check_call([sys.executable, "-m", "ensurepip"])
        process = subprocess.Popen(
            [sys.executable, "-m", "pip"] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
        return process.poll()
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error running pip: {e}")
        return 1

class ONESHOT_OT_install_dependencies(bpy.types.Operator):
    bl_idname = "oneshot.install_dependencies"
    bl_label = "Install Optional Dependencies"
    bl_description = "Install optional Python packages for extended file format support."

    def execute(self, context):
        self.report({'INFO'}, "Installing optional dependencies... Check console for progress.")
        return_code = run_pip(["install"] + optional_dependencies)
        if return_code == 0:
            self.report({'INFO'}, "Optional dependencies installed successfully.")
        else:
            self.report({'ERROR'}, "Failed to install one or more dependencies.")
        return {'FINISHED'}

class ONESHOT_OT_uninstall_dependencies(bpy.types.Operator):
    bl_idname = "oneshot.uninstall_dependencies"
    bl_label = "Uninstall Optional Dependencies"
    bl_description = "Uninstall optional Python packages."

    def execute(self, context):
        self.report({'INFO'}, "Uninstalling optional dependencies... Check console for progress.")
        return_code = run_pip(["uninstall", "-y"] + optional_dependencies)
        if return_code == 0:
            self.report({'INFO'}, "Optional dependencies uninstalled successfully.")
        else:
            self.report({'ERROR'}, "Failed to uninstall one or more dependencies.")
        return {'FINISHED'}

# --- Core Addon Preferences and Operators ---

def _run_installation(context):
    print("oneShot: Starting COLMAP installation worker thread...")
    try:
        addon_path = Path(__file__).parent
        deps_folder = addon_path / "deps"
        deps_folder.mkdir(parents=True, exist_ok=True)

        current_os = platform.system()
        if current_os == "Windows":
            download_url = "https://github.com/colmap/colmap/releases/download/3.12.5/colmap-x64-windows-cuda.zip"
            executable_name = "colmap.exe"
            os_tag = "windows-cuda"
        else:
            print(f"Error: Unsupported OS for COLMAP download: {current_os}")
            return

        zip_file_path = deps_folder / f"colmap_{os_tag}.zip"
        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            with open(zip_file_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(deps_folder)

        colmap_executable = next(deps_folder.glob(f"**/{executable_name}"), None)

        if colmap_executable:
            prefs = context.preferences.addons[__package__].preferences
            prefs.colmap_executable_path = str(colmap_executable)
            print("COLMAP installation successful!")
        else:
            print(f"Error: Could not find {executable_name} after extraction.")

        if zip_file_path.exists():
            zip_file_path.unlink()

    except Exception as e:
        print(f"oneShot Error: {e}")

def _run_ffmpeg_installation(context):
    print("oneShot: Starting FFmpeg installation...")
    try:
        addon_path = Path(__file__).parent
        deps_folder = addon_path / "deps"
        deps_folder.mkdir(parents=True, exist_ok=True)

        current_os = platform.system()
        if current_os == "Windows":
            download_url = "https://github.com/GyanD/codexffmpeg/releases/download/8.0/ffmpeg-8.0-full_build.zip"
            executable_name = "ffmpeg.exe"
        else:
            print(f"Error: Unsupported OS for FFmpeg download: {current_os}")
            return

        zip_file_path = deps_folder / "ffmpeg-release-full.zip"
        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            with open(zip_file_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(deps_folder)

        ffmpeg_executable = next(deps_folder.glob(f"**/{executable_name}"), None)

        if ffmpeg_executable:
            prefs = context.preferences.addons[__package__].preferences
            prefs.ffmpeg_executable_path = str(ffmpeg_executable)
            print("FFmpeg installation successful!")
        else:
            print(f"Error: Could not find {executable_name} after extraction.")

        if zip_file_path.exists():
            zip_file_path.unlink()

    except Exception as e:
        print(f"oneShot Error: {e}")

class ONESHOT_OT_install_ffmpeg(bpy.types.Operator):
    bl_idname = "oneshot.install_ffmpeg"
    bl_label = "Download and Install FFmpeg"
    def execute(self, context):
        threading.Thread(target=_run_ffmpeg_installation, args=(context,)).start()
        self.report({'INFO'}, "FFmpeg installation started. See console for progress.")
        return {'FINISHED'}

class ONESHOT_OT_install_colmap(bpy.types.Operator):
    bl_idname = "oneshot.install_colmap"
    bl_label = "Download and Install COLMAP"
    def execute(self, context):
        threading.Thread(target=_run_installation, args=(context,)).start()
        self.report({'INFO'}, "COLMAP installation started. See console for progress.")
        return {'FINISHED'}

class OneShotPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    colmap_executable_path: bpy.props.StringProperty(
        name="COLMAP Executable Path",
        subtype='FILE_PATH'
    )
    ffmpeg_executable_path: bpy.props.StringProperty(
        name="FFmpeg Executable Path",
        subtype='FILE_PATH'
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "colmap_executable_path")
        layout.operator(ONESHOT_OT_install_colmap.bl_idname, text="Download & Install COLMAP", icon='IMPORT')
        layout.prop(self, "ffmpeg_executable_path")
        layout.operator(ONESHOT_OT_install_ffmpeg.bl_idname, text="Download & Install FFmpeg", icon='IMPORT')

        box = layout.box()
        box.label(text="Optional Importer Dependencies", icon='PACKAGE')
        box.label(text="For other formats, not required for the main COLMAP workflow.")
        row = box.row()
        row.operator(ONESHOT_OT_install_dependencies.bl_idname, icon='CONSOLE')
        row.operator(ONESHOT_OT_uninstall_dependencies.bl_idname, icon='TRASH')

        for dep in optional_dependencies:
            row = box.row()
            row.label(text=f"- {dep}:")
            status_label = "Installed" if is_module_installed(dep) else "Not Installed"
            icon = 'CHECKMARK' if is_module_installed(dep) else 'X'
            row.label(text=status_label, icon=icon)