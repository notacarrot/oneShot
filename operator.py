import bpy

class OneShot_OT_Import(bpy.types.Operator):
    bl_idname = "oneshot.import_operator"
    bl_label = "oneShot Import"

    def execute(self, context):
        print("Importing...")
        return {'FINISHED'}

class OneShot_OT_Export(bpy.types.Operator):
    bl_idname = "oneshot.export_operator"
    bl_label = "oneShot Export"

    def execute(self, context):
        print("Exporting...")
        return {'FINISHED'}

classes = (
    OneShot_OT_Import,
    OneShot_OT_Export,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)