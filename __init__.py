
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
    ui.PhotogrammetrySettings,
    ui.ONESHOT_PT_main_panel,
    operator.ONESHOT_OT_start_photogrammetry,
    operator.ONESHOT_OT_monitor_photogrammetry,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.oneshot_settings = bpy.props.PointerProperty(type=ui.PhotogrammetrySettings)
    bpy.types.WindowManager.oneshot_progress = bpy.props.StringProperty(name="OneShot Progress", default="")

def unregister():
    del bpy.types.Scene.oneshot_settings
    del bpy.types.WindowManager.oneshot_progress

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
