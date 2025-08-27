import bpy
import platform
import requests
import zipfile
import threading
import os
from pathlib import Path

# Worker function for COLMAP installation
def _run_installation(context):
    try:
        # Get addon path
        addon_path = Path(__file__).parent
        deps_folder = addon_path / "deps"
        deps_folder.mkdir(parents=True, exist_ok=True)

        # Check OS
        current_os = platform.system()
        if current_os == "Windows":
            os_tag = "windows-cuda"
            executable_name = "colmap.exe"
        elif current_os == "Linux":
            os_tag = "linux-cuda"
            executable_name = "colmap"
        else:
            print(f"Error: Unsupported operating system: {current_os}")
            return

        print("Fetching latest COLMAP release from GitHub...")
        github_api_url = "https://api.github.com/repos/colmap/colmap/releases/latest"
        response = requests.get(github_api_url)
        response.raise_for_status() # Raise an exception for HTTP errors
        release_data = response.json()

        download_url = None
        for asset in release_data.get("assets", []):
            if os_tag in asset.get("name", "").lower() and asset.get("name", "").endswith(".zip"):
                download_url = asset["browser_download_url"]
                break

        if not download_url:
            print(f"Error: Could not find COLMAP {os_tag} zip file in latest release.")
            return

        # Download
        print("Downloading COLMAP...")
        zip_file_path = deps_folder / f"colmap_{os_tag}.zip"
        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            with open(zip_file_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        # Unzip
        print("Unzipping...")
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(deps_folder)

        # Find Executable
        colmap_executable = None
        for path in deps_folder.glob(f"**/{executable_name}"):
            if path.is_file():
                colmap_executable = path
                break

        if colmap_executable:
            # Save Path to preferences
            prefs = context.preferences.addons[__package__].preferences
            prefs.colmap_executable_path = str(colmap_executable)
            print("COLMAP installation successful!")
        else:
            print(f"Error: Could not find {executable_name} after extraction.")

        # Cleanup
        if zip_file_path.exists():
            zip_file_path.unlink()
            print("Cleaned up downloaded zip file.")

    except requests.exceptions.RequestException as e:
        print(f"Network error during COLMAP installation: {e}")
    except zipfile.BadZipFile:
        print("Error: Downloaded file is not a valid zip file.")
    except Exception as e:
        print(f"An unexpected error occurred during COLMAP installation: {e}")

class ONESHOT_OT_install_colmap(bpy.types.Operator):
    bl_idname = "oneshot.install_colmap"
    bl_label = "Download and Install COLMAP"
    bl_description = "Download and install COLMAP for your operating system"

    def execute(self, context):
        # Start installation in a new thread to avoid blocking Blender UI
        install_thread = threading.Thread(target=_run_installation, args=(context,))
        install_thread.start()
        self.report({'INFO'}, "COLMAP installation started in background. Check console for progress.")
        return {'FINISHED'}

class OneShotPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    colmap_executable_path: bpy.props.StringProperty(
        name="COLMAP Executable Path",
        subtype='FILE_PATH',
        description="Path to the COLMAP executable (colmap.bat or colmap.exe)"
    )

    def draw(self, context):
        layout = self.layout

        # Display the executable path property
        layout.prop(self, "colmap_executable_path")

        # Button to trigger the installation operator
        row = layout.row()
        row.operator(ONESHOT_OT_install_colmap.bl_idname, text="Download & Install COLMAP", icon='IMPORT')