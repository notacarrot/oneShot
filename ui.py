import bpy

class VIEW3D_PT_oneShot_main_panel(bpy.types.Panel):
    bl_label = "oneShot"
    bl_idname = "VIEW3D_PT_oneShot_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'oneShot'

    def draw(self, context):
        layout = self.layout
        layout.label(text="oneShot Main Panel")
        layout.operator("oneshot.import_operator")
        layout.operator("oneshot.export_operator")

classes = (
    VIEW3D_PT_oneShot_main_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)