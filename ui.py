import bpy
from bpy.types import PropertyGroup, Panel
from bpy.props import StringProperty, BoolProperty, EnumProperty

class PhotogrammetrySettings(PropertyGroup):
    video_path: StringProperty(
        name="Video File",
        subtype='FILE_PATH',
        description="Path to the input video file"
    )
    show_advanced: BoolProperty(
        name="Show Advanced Settings",
        default=False
    )
    image_format: EnumProperty(
        name="Image Format",
        items=[
            ('PNG', "PNG", "Portable Network Graphics"),
            ('JPG', "JPG", "Joint Photographic Experts Group"),
        ],
        default='PNG'
    )
    colmap_quality: EnumProperty(
        name="COLMAP Quality",
        items=[
            ('LOW', "Low", "Low quality COLMAP reconstruction"),
            ('MEDIUM', "Medium", "Medium quality COLMAP reconstruction"),
            ('HIGH', "High", "High quality COLMAP reconstruction"),
            ('EXTREME', "Extreme", "Extreme quality COLMAP reconstruction"),
        ],
        default='MEDIUM'
    )
    delete_workspace: BoolProperty(
        name="Delete Workspace After Completion",
        description="Delete temporary files and workspace after photogrammetry is complete",
        default=True
    )

class ONESHOT_PT_main_panel(Panel):
    bl_label = "OneShot Photogrammetry"
    bl_idname = "ONESHOT_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "OneShot"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        wm = context.window_manager
        settings = scene.oneshot_settings

        layout.prop(settings, "video_path")

        layout.operator("oneshot.start_photogrammetry", text="Generate 3D Scene", icon='PLAY')

        box = layout.box()
        row = box.row()
        row.prop(settings, "show_advanced",
                 icon='DOWNARROW_HLT' if settings.show_advanced else 'RIGHTARROW',
                 icon_only=True, emboss=False)
        row.label(text="Advanced Settings")

        if settings.show_advanced:
            box.prop(settings, "image_format")
            box.prop(settings, "colmap_quality")
            box.prop(settings, "delete_workspace")

        layout.separator()
        layout.label(text=f"Progress: {wm.oneshot_progress}")
