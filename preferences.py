import bpy
from .importer.operators.colmap_install_op import OT_install_colmap

class OneShotAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    colmap_executable_path: bpy.props.StringProperty(
        name="COLMAP Executable Path",
        subtype='FILE_PATH',
        default=''
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "colmap_executable_path")
        layout.operator("colmap.install")

classes = (
    OT_install_colmap,
    OneShotAddonPreferences,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)