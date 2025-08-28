import os
import bpy
from bpy.types import PropertyGroup, Panel
from bpy.props import StringProperty, BoolProperty, EnumProperty

class PhotogrammetrySettings(PropertyGroup):
    video_input_path: StringProperty(
        name="Video File",
        subtype='FILE_PATH',
        description="Path to the input video file"
    ) # type: ignore
    image_output_folder: StringProperty(
        name="Output Folder for Extracted Images",
        subtype='DIR_PATH',
        description="Directory where extracted frames will be saved",
        default=os.path.join(bpy.app.tempdir, "oneshot_frames")
    ) # type: ignore
    image_input_folder: StringProperty(
        name="Input Folder for Reconstruction",
        subtype='DIR_PATH',
        description="Directory containing images for 3D reconstruction",
        default=os.path.join(bpy.app.tempdir, "oneshot_frames")
    ) # type: ignore
    reconstruction_output_folder: StringProperty(
        name="Reconstruction Output Folder",
        subtype='DIR_PATH',
        description="Folder to store the COLMAP reconstruction files"
    ) # type: ignore
    show_advanced: BoolProperty(
        name="Show Advanced Settings",
        default=False
    ) # type: ignore
    image_format: EnumProperty(
        name="Image Format",
        items=[
            ('PNG', "PNG", "Portable Network Graphics"),
            ('JPG', "JPG", "Joint Photographic Experts Group"),
        ],
        default='PNG'
    ) # type: ignore
    colmap_quality: EnumProperty(
        name="COLMAP Quality",
        items=[
            ('LOW', "Low", "Low quality COLMAP reconstruction"),
            ('MEDIUM', "Medium", "Medium quality COLMAP reconstruction"),
            ('HIGH', "High", "High quality COLMAP reconstruction"),
            ('EXTREME', "Extreme", "Extreme quality COLMAP reconstruction"),
        ],
        default='MEDIUM'
    ) # type: ignore
    delete_workspace: BoolProperty(
        name="Delete Workspace After Completion",
        description="Delete temporary files and workspace after photogrammetry is complete",
        default=True
    ) # type: ignore

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

        # Section 1: Extract Frames
        box1 = layout.box()
        box1.label(text="Step 1: Extract Frames", icon='FILE_MOVIE')
        box1.prop(settings, "video_input_path")
        box1.prop(settings, "image_output_folder")
        box1.operator("oneshot.start_extraction", text="Extract Frames to Folder", icon='RENDER_ANIMATION')

        # Section 2: Reconstruct Scene
        box2 = layout.box()
        box2.label(text="Step 2: Reconstruct Scene", icon='OUTLINER_OB_CAMERA')
        box2.prop(settings, "image_input_folder")
        box2.prop(settings, "reconstruction_output_folder")
        box2.operator("oneshot.reconstruct_scene", text="Generate 3D Scene", icon='PLAY')

        # Advanced Settings (now part of Step 2)
        box_advanced = box2.box()
        row = box_advanced.row()
        row.prop(settings, "show_advanced",
                 icon='DOWNARROW_HLT' if settings.show_advanced else 'RIGHTARROW',
                 icon_only=True, emboss=False)
        row.label(text="Advanced Settings")

        if settings.show_advanced:
            box_advanced.prop(settings, "image_format")
            box_advanced.prop(settings, "colmap_quality")
            box_advanced.prop(settings, "delete_workspace")

        layout.separator()
        layout.label(text=f"Progress: {wm.oneshot_progress}")
        layout.label(text=wm.oneshot_progress_detail)
