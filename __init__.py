
bl_info = {
    "name": "oneShot",
    "author": "notacarrrot",
    "version": (4, 0, 0),
    "blender": (4, 0, 0),
    "category": "Import-Export",
    "description": "A modular Blender addon for photogrammetry workflows.",
    "doc_url": "",
    "tracker_url": "",
}

import bpy
from . import preferences
from . import ui
from . import operator

# List of classes to register
classes = (
    preferences.OneShotPreferences,
    preferences.ONESHOT_OT_install_colmap,
    preferences.ONESHOT_OT_install_ffmpeg,
    ui.PhotogrammetrySettings,
    ui.ONESHOT_PT_main_panel,
    operator.ONESHOT_OT_start_extraction,
    operator.ONESHOT_OT_monitor_extraction,
    operator.ONESHOT_OT_reconstruct_scene,
    operator.ONESHOT_OT_reconstruct_monitor,
)

def register():
    print("oneShot: Registering addon...")
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.oneshot_settings = bpy.props.PointerProperty(type=ui.PhotogrammetrySettings)
    bpy.types.WindowManager.oneshot_progress = bpy.props.StringProperty(name="OneShot Progress", default="")
    bpy.types.WindowManager.oneshot_progress_detail = bpy.props.StringProperty(name="OneShot Progress Detail", default="")
    

def unregister():
    print("oneShot: Unregistering addon...")
    del bpy.types.Scene.oneshot_settings
    del bpy.types.WindowManager.oneshot_progress
    del bpy.types.WindowManager.oneshot_progress_detail
    

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
