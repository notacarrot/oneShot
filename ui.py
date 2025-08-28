import os
import bpy
from bpy.types import PropertyGroup, Panel
from bpy.props import StringProperty, BoolProperty, EnumProperty, FloatProperty, IntProperty

class PhotogrammetrySettings(PropertyGroup):
    input_path: StringProperty(
        name="Input Video or Image Folder",
        subtype='FILE_PATH',
        description="Path to the input video file or image folder"
    )
    output_path: StringProperty(
        name="Output Scene Folder",
        subtype='DIR_PATH',
        description="Directory where the scene and reconstruction will be saved"
    )
    colmap_model_path: StringProperty(
        name="COLMAP Model Path",
        subtype='DIR_PATH',
        description="Path to the COLMAP model folder for direct import"
    )
    image_dp: StringProperty(
        name="Image Directory Path",
        subtype='DIR_PATH',
        description="Path to the directory containing the images"
    )

    # Advanced Settings
    use_workspace_images: BoolProperty(name="Use Workspace Images", default=True)
    import_cameras: BoolProperty(name="Import Cameras", default=True)
    initial_camera_extent: FloatProperty(name="Initial Camera Extent (in Blender Units)", default=1.0)
    add_background_image_for_each_camera: BoolProperty(name="Add a Background Image for each Camera", default=True)
    add_image_plane_for_each_camera: BoolProperty(name="Add an Image Plane for each Camera", default=False)
    add_depth_maps: BoolProperty(name="Add Depth Maps (EXPERIMENTAL)", default=False)
    add_camera_motion_as_animation: BoolProperty(name="Add Camera Motion as Animation", default=True)
    add_background_images_for_animated_camera: BoolProperty(name="Add Background Images for the Animated Camera", default=True)
    adjust_frame_numbers_of_camera_animation: BoolProperty(name="Adjust Frame Numbers of Camera Animation", default=True)
    interpolation_type: EnumProperty(name="Interpolation", items=[('LINEAR', 'Linear', ''), ('BEZIER', 'Bezier', ''), ('SINE', 'Sine', '')], default='LINEAR')
    remove_rotation_discontinuities: BoolProperty(name="Remove Rotation Discontinuities", default=True)
    suppress_distortion_warnings: BoolProperty(name="Suppress Distortion Warnings", default=True)
    adjust_render_settings: BoolProperty(name="Adjust Render Settings", default=True)
    import_points: BoolProperty(name="Import Points", default=True)
    point_cloud_display_sparsity: IntProperty(name="Point Cloud Display Sparsity", default=1, min=1)
    center_data_around_origin: BoolProperty(name="Center Data Around Origin", default=False)
    draw_points_in_3d_view_with_opengl: BoolProperty(name="Draw Points in the 3D View with OpenGL", default=True)
    add_point_data_to_point_cloud_handle: BoolProperty(name="Add point data to the point cloud handle.", default=True)
    initial_point_size: IntProperty(name="Initial Point Size", default=5, min=1)
    add_points_as_mesh_object: BoolProperty(name="Add Points as Mesh Object", default=False)
    import_mesh: BoolProperty(name="Import Mesh", default=False)
    adjust_clipping_distance: BoolProperty(name="Adjust Clipping Distance", default=False)

class ONESHOT_PT_WorkflowPanel(Panel):
    bl_label = "oneShot Workflow"
    bl_idname = "ONESHOT_PT_WorkflowPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "OneShot"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.oneshot_settings

        layout.prop(settings, "input_path")
        layout.prop(settings, "output_path")

        layout.operator("oneshot.reconstruct_scene", text="Generate Scene", icon='PLAY')

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

        box_camera = layout.box()
        box_camera.label(text="Import Cameras")
        box_camera.prop(settings, "import_cameras")
        box_camera.prop(settings, "initial_camera_extent")
        box_camera.prop(settings, "add_background_image_for_each_camera")
        box_camera.prop(settings, "add_image_plane_for_each_camera")
        box_camera.prop(settings, "add_depth_maps")
        box_camera.prop(settings, "suppress_distortion_warnings")
        box_camera.prop(settings, "adjust_render_settings")

        box_anim = layout.box()
        box_anim.label(text="Add Camera Motion as Animation")
        box_anim.prop(settings, "add_camera_motion_as_animation")
        box_anim.prop(settings, "add_background_images_for_animated_camera")
        box_anim.prop(settings, "adjust_frame_numbers_of_camera_animation")
        box_anim.prop(settings, "interpolation_type")
        box_anim.prop(settings, "remove_rotation_discontinuities")

        box_points = layout.box()
        box_points.label(text="Import Points")
        box_points.prop(settings, "import_points")
        box_points.prop(settings, "point_cloud_display_sparsity")
        box_points.prop(settings, "center_data_around_origin")
        box_points.prop(settings, "draw_points_in_3d_view_with_opengl")
        box_points.prop(settings, "add_point_data_to_point_cloud_handle")
        box_points.prop(settings, "initial_point_size")
        box_points.prop(settings, "add_points_as_mesh_object")

        layout.prop(settings, "import_mesh")
        layout.prop(settings, "adjust_clipping_distance")
