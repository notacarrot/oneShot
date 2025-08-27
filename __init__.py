bl_info = {
    "name": "oneShot",
    "author": "Swagat Nayak",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "View3D > N",
    "description": "oneShot",
    "warning": "",
    "wiki_url": "",
    "category": "Import-Export",
}

import bpy
from . import preferences
from . import ui
from . import operator

def register():
    preferences.register()
    ui.register()
    operator.register()
    bpy.types.WindowManager.photogrammetry_progress = bpy.props.StringProperty(default="")

def unregister():
    preferences.unregister()
    ui.unregister()
    operator.unregister()
    del bpy.types.WindowManager.photogrammetry_progress

if __name__ == "__main__":
    register()