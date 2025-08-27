import bpy
import os
import threading
import requests
import zipfile
import addon_utils
import platform
from ..blender_utility.retrieval_utility import get_colmap_url

class OT_install_colmap(bpy.types.Operator):
    bl_idname = "colmap.install"
    bl_label = "Install COLMAP"
    bl_description = "Downloads and installs the latest version of COLMAP."

    _timer = None
    _thread = None
    _progress = 0

    def execute(self, context):
        self._thread = threading.Thread(target=self.install_colmap_thread, args=(context,))
        self._thread.start()
        self._timer = context.window_manager.event_timer_add(0.1, window=context.window)
        context.window_manager.modal_handler_add(self)
        context.window_manager.progress_begin(0, 100)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type == 'TIMER':
            if self._thread and self._thread.is_alive():
                context.window_manager.progress_update(self._progress)
            else:
                context.window_manager.progress_end()
                self.cancel(context)
                return {'FINISHED'}
        return {'PASS_THROUGH'}

    def cancel(self, context):
        context.window_manager.event_timer_remove(self._timer)
        self._timer = None

    def install_colmap_thread(self, context):
        try:
            self.report({'INFO'}, "Starting COLMAP installation.")
            
            # 1. Get URL
            url = get_colmap_url()
            if not url:
                self.report({'ERROR'}, "Could not get COLMAP download URL.")
                return

            # 2. Get addon directory and create deps folder
            addon_name = "oneShot"
            addon_dir = ""
            for mod in addon_utils.modules():
                if mod.bl_info['name'] == addon_name:
                    addon_dir = os.path.dirname(mod.__file__)
                    break
            
            deps_dir = os.path.join(addon_dir, "deps")
            os.makedirs(deps_dir, exist_ok=True)
            
            zip_path = os.path.join(deps_dir, "colmap.zip")

            # 3. Download
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(zip_path, 'wb') as f:
                    total_length = int(r.headers.get('content-length'))
                    dl = 0
                    for chunk in r.iter_content(chunk_size=8192):
                        dl += len(chunk)
                        f.write(chunk)
                        self._progress = int(50 * dl / total_length)

            # 4. Extract
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(deps_dir)
            os.remove(zip_path)
            
            self._progress = 75

            # 5. Find executable
            executable_name = "colmap.exe" if platform.system() == "Windows" else "colmap"
            colmap_executable_path = None
            for root, dirs, files in os.walk(deps_dir):
                if executable_name in files:
                    colmap_executable_path = os.path.join(root, executable_name)
                    break
            
            if not colmap_executable_path:
                self.report({'ERROR'}, "Could not find COLMAP executable after extraction.")
                return

            # 6. Save path to preferences
            addon_prefs = context.preferences.addons[addon_name].preferences
            addon_prefs.colmap_executable_path = colmap_executable_path
            
            self._progress = 100
            self.report({'INFO'}, "COLMAP installation successful.")

        except Exception as e:
            self.report({'ERROR'}, f"COLMAP installation failed: {e}")