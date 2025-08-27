import bpy
import platform
import requests
import zipfile
import threading
import os
from pathlib import Path

# Worker function for COLMAP installation
def _run_installation(context):
    print("oneShot: Starting COLMAP installation worker thread...")
    try:
        # Get addon path
        addon_path = Path(__file__).parent
        deps_folder = addon_path / "deps"
        print(f"oneShot: Addon path: {addon_path}, Dependencies folder: {deps_folder}")
        deps_folder.mkdir(parents=True, exist_ok=True)
        print("oneShot: Dependencies folder ensured to exist.")

        # Check OS
        current_os = platform.system()
        print(f"oneShot: Detected OS: {current_os}")
        if current_os == "Windows":
            os_tag = "windows-cuda"
            executable_name = "colmap.exe"
        elif current_os == "Linux":
            os_tag = "linux-cuda"
            executable_name = "colmap"
        else:
            print(f"Error: Unsupported operating system: {current_os}")
            return

        print("oneShot: Fetching latest COLMAP release from GitHub...")
        github_api_url = "https://api.github.com/repos/colmap/colmap/releases/latest"
        print(f"oneShot: Requesting URL: {github_api_url}")
        response = requests.get(github_api_url)
        response.raise_for_status() # Raise an exception for HTTP errors
        release_data = response.json()
        print("oneShot: Successfully fetched GitHub release data.")

        download_url = None
        for asset in release_data.get("assets", []):
            if os_tag in asset.get("name", "").lower() and asset.get("name", "").endswith(".zip"):
                download_url = asset["browser_download_url"]
                break

        if not download_url:
            print(f"Error: Could not find COLMAP {os_tag} zip file in latest release.")
            return
        print(f"oneShot: Found download URL: {download_url}")

        # Download
        print("oneShot: Downloading COLMAP...")
        zip_file_path = deps_folder / f"colmap_{os_tag}.zip"
        print(f"oneShot: Downloading to: {zip_file_path}")
        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            with open(zip_file_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print("oneShot: Download complete.")

        # Unzip
        print("oneShot: Unzipping...")
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(deps_folder)
        print("oneShot: Unzipping complete.")

        # Find Executable
        print(f"oneShot: Searching for {executable_name} in {deps_folder}...")
        colmap_executable = None
        for path in deps_folder.glob(f"**/{executable_name}"):
            if path.is_file():
                colmap_executable = path
                break

        if colmap_executable:
            print(f"oneShot: Found executable at: {colmap_executable}")
            # Save Path to preferences
            print(f"oneShot: Saving executable path to preferences: {colmap_executable}")
            prefs = context.preferences.addons[__package__].preferences
            prefs.colmap_executable_path = str(colmap_executable)
            print("COLMAP installation successful!")
        else:
            print(f"Error: Could not find {executable_name} after extraction.")

        # Cleanup
        if zip_file_path.exists():
            print(f"oneShot: Cleaning up downloaded zip file: {zip_file_path}")
            zip_file_path.unlink()
            print("Cleaned up downloaded zip file.")

    except requests.exceptions.RequestException as e:
        print(f"oneShot Error: Network error during COLMAP installation: {e}")
    except zipfile.BadZipFile:
        print("oneShot Error: Downloaded file is not a valid zip file.")
    except Exception as e:
        print(f"oneShot Error: An unexpected error occurred during COLMAP installation: {e}")

# Worker function for FFmpeg installation
def _run_ffmpeg_installation(context):
    print("oneShot: Starting FFmpeg installation worker thread...")
    try:
        # Get addon path
        addon_path = Path(__file__).parent
        deps_folder = addon_path / "deps"
        print(f"oneShot: Addon path: {addon_path}, Dependencies folder: {deps_folder}")
        deps_folder.mkdir(parents=True, exist_ok=True)
        print("oneShot: Dependencies folder ensured to exist.")

        # Check OS
        current_os = platform.system()
        print(f"oneShot: Detected OS: {current_os}")
        if current_os == "Windows":
            # Using gyan.dev for static builds
            download_url = "https://github.com/GyanD/codexffmpeg/releases/download/8.0/ffmpeg-8.0-full_build.zip" # UPDATED URL
            executable_name = "ffmpeg.exe"
        else:
            print(f"Error: Unsupported operating system for FFmpeg download: {current_os}")
            return

        print(f"oneShot: Downloading FFmpeg from {download_url}...")
        zip_file_path = deps_folder / "ffmpeg-release-full.zip" # UPDATED FILENAME
        print(f"oneShot: Downloading to: {zip_file_path}")
        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            with open(zip_file_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print("oneShot: Download complete.")

        # Unzip .zip file (standard zipfile module)
        print("oneShot: Extracting FFmpeg...")
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref: # UPDATED EXTRACTION LOGIC
            zip_ref.extractall(deps_folder)
        print("oneShot: Extraction complete.")

        # Find Executable
        print(f"oneShot: Searching for {executable_name} in {deps_folder}...")
        ffmpeg_executable = None
        for path in deps_folder.glob(f"**/{executable_name}"):
            if path.is_file():
                ffmpeg_executable = path
                break

        if ffmpeg_executable:
            print(f"oneShot: Found executable at: {ffmpeg_executable}")
            # Save Path to preferences
            print(f"oneShot: Saving executable path to preferences: {ffmpeg_executable}")
            prefs = context.preferences.addons[__package__].preferences
            prefs.ffmpeg_executable_path = str(ffmpeg_executable)
            print("FFmpeg installation successful!")
        else:
            print(f"Error: Could not find {executable_name} after extraction.")

        # Cleanup
        if zip_file_path.exists():
            print(f"oneShot: Cleaning up downloaded zip file: {zip_file_path}") # UPDATED MESSAGE
            zip_file_path.unlink()
            print("Cleaned up downloaded zip file.") # UPDATED MESSAGE

    except requests.exceptions.RequestException as e:
        print(f"oneShot Error: Network error during FFmpeg installation: {e}")
    except zipfile.BadZipFile:
        print("oneShot Error: Downloaded file is not a valid zip file.") # ADDED THIS EXCEPTION
    except Exception as e:
        print(f"oneShot Error: An unexpected error occurred during FFmpeg installation: {e}")

class ONESHOT_OT_install_ffmpeg(bpy.types.Operator):
    bl_idname = "oneshot.install_ffmpeg"
    bl_label = "Download and Install FFmpeg"
    bl_description = "Download and install FFmpeg for your operating system"

    def execute(self, context):
        print("oneShot: ONESHOT_OT_install_ffmpeg operator executed.")
        # Start installation in a new thread to avoid blocking Blender UI
        install_thread = threading.Thread(target=_run_ffmpeg_installation, args=(context,))
        install_thread.start()
        print("oneShot: FFmpeg installation thread started.")
        self.report({'INFO'}, "FFmpeg installation started in background. Check console for progress.")
        return {'FINISHED'}

class ONESHOT_OT_install_colmap(bpy.types.Operator):
    bl_idname = "oneshot.install_colmap"
    bl_label = "Download and Install COLMAP"
    bl_description = "Download and install COLMAP for your operating system"

    def execute(self, context):
        print("oneShot: ONESHOT_OT_install_colmap operator executed.")
        # Start installation in a new thread to avoid blocking Blender UI
        install_thread = threading.Thread(target=_run_installation, args=(context,))
        install_thread.start()
        print("oneShot: COLMAP installation thread started.")
        self.report({'INFO'}, "COLMAP installation started in background. Check console for progress.")
        return {'FINISHED'}

class OneShotPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    colmap_executable_path: bpy.props.StringProperty(
        name="COLMAP Executable Path",
        subtype='FILE_PATH',
        description="Path to the COLMAP executable (colmap.bat or colmap.exe)"
    )
    ffmpeg_executable_path: bpy.props.StringProperty(
        name="FFmpeg Executable Path",
        subtype='FILE_PATH',
        description="Path to the FFmpeg executable (ffmpeg.exe)"
    )

    def draw(self, context):
        layout = self.layout

        # Display the executable path property
        layout.prop(self, "colmap_executable_path")

        # Button to trigger the installation operator
        row = layout.row()
        row.operator(ONESHOT_OT_install_colmap.bl_idname, text="Download & Install COLMAP", icon='IMPORT')

        # NEW SECTION FOR FFMPEG
        layout.prop(self, "ffmpeg_executable_path")
        row = layout.row()
        row.operator(ONESHOT_OT_install_ffmpeg.bl_idname, text="Download & Install FFmpeg", icon='IMPORT')