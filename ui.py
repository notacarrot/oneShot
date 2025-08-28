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
    colmap_model_path: StringProperty(
        name="COLMAP Model Path",
        subtype='FILE_PATH',
        description="Path to the COLMAP model folder (containing cameras.bin, images.bin, points3D.bin)"
    ) # type: ignore

    # Advanced settings
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

    import_cameras: BoolProperty(name="Import Cameras", default=True)
    add_background_image_for_each_camera: BoolProperty(name="Add Background Images", default=True)
    add_camera_motion_as_animation: BoolProperty(name="Animate Cameras", default=True)
    import_points: BoolProperty(name="Import Points", default=True)
    add_points_as_mesh_object: BoolProperty(name="Add Points as Mesh Object", default=False)

class ONESHOT_PT_WorkflowPanel(Panel):
    bl_label = "oneShot Workflow"
    bl_idname = "ONESHOT_PT_WorkflowPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "OneShot"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.oneshot_settings

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

        layout.separator()
        wm = context.window_manager
        layout.label(text=f"Progress: {wm.oneshot_progress}")
        layout.label(text=wm.oneshot_progress_detail)

class ONESHOT_PT_DirectImportPanel(Panel):
    bl_label = "Direct Import"
    bl_idname = "ONESHOT_PT_DirectImportPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "OneShot"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.oneshot_settings

        layout.label(text="Import Pre-existing COLMAP Model")
        layout.prop(settings, "colmap_model_path")
        layout.operator("oneshot.import_colmap_model", text="Import Model", icon='IMPORT')

class ONESHOT_PT_AdvancedSettingsPanel(Panel):
    bl_label = "Advanced Settings"
    bl_idname = "ONESHOT_PT_AdvancedSettingsPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "OneShot"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        settings = context.scene.oneshot_settings

        col = layout.column()
        
        col.label(text="Reconstruction:")
        col.prop(settings, "image_format")
        col.prop(settings, "colmap_quality")
        col.prop(settings, "delete_workspace")
        
        col.separator()
        
        col.label(text="Camera Import Options:")
        col.prop(settings, "import_cameras")
        col.prop(settings, "add_background_image_for_each_camera")
        col.prop(settings, "add_camera_motion_as_animation")
        
        col.separator()

        col.label(text="Point Cloud Options:")
        col.prop(settings, "import_points")
        col.prop(settings, "add_points_as_mesh_object")
