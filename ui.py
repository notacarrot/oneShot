import bpy

class PhotogrammetrySettings(bpy.types.PropertyGroup):
    video_path: bpy.props.StringProperty(
        name="Video Path",
        subtype='FILE_PATH'
    )
    show_advanced: bpy.props.BoolProperty(
        name="Advanced Settings",
        default=False
    )
    image_format: bpy.props.EnumProperty(
        name="Image Format",
        items=[
            ('PNG', "PNG", "PNG format"),
            ('JPG', "JPG", "JPG format")
        ]
    )
    colmap_quality: bpy.props.EnumProperty(
        name="COLMAP Quality",
        items=[
            ('LOW', "Low", "Low quality"),
            ('MEDIUM', "Medium", "Medium quality"),
            ('HIGH', "High", "High quality"),
            ('EXTREME', "Extreme", "Extreme quality")
        ]
    )
    delete_workspace: bpy.props.BoolProperty(
        name="Delete Workspace on Finish",
        default=True
    )

class VIEW3D_PT_oneShot_main_panel(bpy.types.Panel):
    bl_label = "oneShot"
    bl_idname = "VIEW3D_PT_oneShot_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'oneShot'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.photogrammetry_settings

        layout.prop(settings, "video_path")
        
        op = layout.operator("oneshot.generate_scene", text="Generate 3D Scene", icon='PLAY')
        
        row = layout.row()
        icon = 'DOWNARROW_HLT' if settings.show_advanced else 'RIGHTARROW'
        row.prop(settings, "show_advanced", icon=icon, text="Advanced Settings", emboss=False)
        
        if settings.show_advanced:
            box = layout.box()
            box.prop(settings, "image_format")
            box.prop(settings, "colmap_quality")
            box.prop(settings, "delete_workspace")
            
        layout.label(text=context.window_manager.photogrammetry_progress)

classes = (
    PhotogrammetrySettings,
    VIEW3D_PT_oneShot_main_panel,
)

def register():
    bpy.types.Scene.photogrammetry_settings = bpy.props.PointerProperty(type=PhotogrammetrySettings)
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    del bpy.types.Scene.photogrammetry_settings
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
