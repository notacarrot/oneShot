import bpy
import threading
import time
import subprocess
import os
import shutil
from pathlib import Path
from .importer import import_colmap_scene

_background_thread = None

def _run_ffmpeg_extraction(context, video_path, output_folder, ffmpeg_path, image_format):
    try:
        context.window_manager.oneshot_progress = "Step 1: Extracting Frames..."
        
        output_pattern = os.path.join(output_folder, f"%04d.{image_format}")
        command = [
            ffmpeg_path,
            "-i", video_path,
            output_pattern
        ]

        print(f"oneShot: Running FFmpeg command: {' '.join(command)}")
        
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')

        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                line = output.strip()
                print(line)
                context.window_manager.oneshot_progress_detail = line
        
        rc = process.poll()
        if rc != 0:
            context.window_manager.oneshot_progress = "Error: Frame extraction failed."
            print(f"oneShot: FFmpeg command failed with return code {rc}")
            return
            
        context.window_manager.oneshot_progress = "Frame Extraction Complete!"

    except Exception as e:
        context.window_manager.oneshot_progress = "Error during frame extraction. Check console."
        print(f"oneShot: An unexpected error occurred during FFmpeg execution: {e}")

def _run_colmap(context, colmap_executable_path: str, image_directory: str, workspace_path: Path) -> Path | None:
    try:
        print(f"oneShot: _run_colmap: Starting COLMAP execution. Executable: {colmap_executable_path}, Images: {image_directory}, Workspace: {workspace_path})")
        database_path = workspace_path / "database.db"
        
        sparse_path = workspace_path / "sparse"
        sparse_path.mkdir(parents=True, exist_ok=True)

        commands = [
            [colmap_executable_path, "feature_extractor", "--database_path", str(database_path), "--image_path", str(image_directory), "--ImageReader.single_camera", "1", "--SiftExtraction.use_gpu", "1"],
            [colmap_executable_path, "sequential_matcher", "--database_path", str(database_path)],
            [colmap_executable_path, "mapper", "--database_path", str(database_path), "--image_path", str(image_directory), "--output_path", str(sparse_path)],
        ]

        for cmd in commands:
            print(f"oneShot: _run_colmap: Running COLMAP command: {' '.join(cmd)}")
            
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')

            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    line = output.strip()
                    print(line)
                    if context:
                        context.window_manager.oneshot_progress_detail = line

            rc = process.poll()
            if rc != 0:
                print(f"oneShot: _run_colmap Error: COLMAP command failed with return code {rc}")
                return None
        
        print("oneShot: _run_colmap: COLMAP execution successful.")
        
        reconstruction_path = sparse_path / "0"
        if reconstruction_path.exists():
            print(f"oneShot: _run_colmap: Sparse reconstruction found at: {reconstruction_path}")
            return reconstruction_path
        else:
            if (sparse_path / "cameras.bin").exists():
                print(f"oneShot: _run_colmap: Found model files directly in sparse folder. Returning: {sparse_path}")
                return sparse_path
            print(f"oneShot: _run_colmap Error: Sparse reconstruction directory not found at: {reconstruction_path}")
            return None

    except Exception as e:
        print(f"oneShot: _run_colmap Error: An error occurred during COLMAP execution: {e}")
        return None

def run_photogrammetry_process(context, settings, colmap_exe_path: str, image_dir: str, workspace_dir: Path, delete_workspace: bool):
    try:
        print("oneShot: run_photogrammetry_process: Starting background photogrammetry process.")
        
        context.window_manager.oneshot_progress = "Step 2/3: Running COLMAP Reconstruction..."
        print("oneShot: run_photogrammetry_process: Calling _run_colmap...")
        sparse_reconstruction_path = _run_colmap(context, colmap_exe_path, image_dir, workspace_dir)
        if sparse_reconstruction_path is None:
            context.window_manager.oneshot_progress = "Error: COLMAP reconstruction failed."
            print("oneShot: run_photogrammetry_process Error: COLMAP reconstruction failed.")
            return

        context.window_manager.oneshot_progress = "Step 3/3: Importing Scene..."
        print("oneShot: run_photogrammetry_process: Calling import_colmap_scene...")
        if not import_colmap_scene(
            reconstruction_dir_path=str(sparse_reconstruction_path),
            import_cameras=settings.import_cameras,
            add_background_image=settings.add_background_image_for_each_camera,
            add_camera_motion=settings.add_camera_motion_as_animation,
            import_points=settings.import_points,
            add_points_as_mesh_object=settings.add_points_as_mesh_object
        ):
            context.window_manager.oneshot_progress = "Error: Scene import failed."
            print("oneShot: run_photogrammetry_process Error: Scene import failed.")
            return
        
        context.window_manager.oneshot_progress = "Success! Scene Imported."
        print("oneShot: run_photogrammetry_process: Photogrammetry process finished.")

    except Exception as e:
        print(f"oneShot: run_photogrammetry_process Error: An unexpected error occurred: {e}")
    finally:
        print("oneShot: run_photogrammetry_process: Entering finally block for cleanup.")
        if workspace_dir and workspace_dir.exists():
            if delete_workspace:
                images_path = workspace_dir / "images"
                if images_path.exists() and images_path.is_dir():
                    shutil.rmtree(images_path)
                    print(f"oneShot: run_photogrammetry_process: Cleaned up images subfolder: {images_path}")
                else:
                    print(f"oneShot: run_photogrammetry_process: No images subfolder to clean up at {images_path}.")
            else:
                print(f"oneShot: run_photogrammetry_process: Workspace retained at {workspace_dir}")

class ONESHOT_OT_start_extraction(bpy.types.Operator):
    bl_idname = "oneshot.start_extraction"
    bl_label = "Extract Frames"
    bl_description = "Extracts frames from the video to the specified folder using FFmpeg"

    def execute(self, context):
        settings = context.scene.oneshot_settings
        prefs = context.preferences.addons[__package__].preferences

        video_input_path = settings.video_input_path
        image_output_folder = settings.image_output_folder
        ffmpeg_executable_path = prefs.ffmpeg_executable_path
        image_format = settings.image_format.lower()

        if not all([video_input_path, image_output_folder, ffmpeg_executable_path]):
            self.report({'ERROR'}, "One or more paths are not set.")
            return {'CANCELLED'}

        if not os.path.exists(image_output_folder):
            os.makedirs(image_output_folder)

        thread = threading.Thread(
            target=_run_ffmpeg_extraction,
            args=(context, video_input_path, image_output_folder, ffmpeg_executable_path, image_format)
        )
        thread.start()

        global _background_thread
        _background_thread = thread

        return bpy.ops.oneshot.monitor_extraction('INVOKE_DEFAULT')

class ONESHOT_OT_monitor_extraction(bpy.types.Operator):
    bl_idname = "oneshot.monitor_extraction"
    bl_label = "Monitor Extraction"

    _timer = None
    _thread = None

    def invoke(self, context, event):
        global _background_thread
        self._thread = _background_thread

        if not self._thread or not self._thread.is_alive():
            self.report({'INFO'}, "Extraction process not running.")
            return {'FINISHED'}

        self._timer = context.window_manager.event_timer_add(0.1, window=context.window)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type == 'TIMER':
            if not self._thread.is_alive():
                context.window_manager.event_timer_remove(self._timer)
                global _background_thread
                _background_thread = None
                return {'FINISHED'}
            else:
                context.area.tag_redraw()
        return {'PASS_THROUGH'}

    def cancel(self, context):
        context.window_manager.event_timer_remove(self._timer)

class ONESHOT_OT_reconstruct_scene(bpy.types.Operator):
    bl_idname = "oneshot.reconstruct_scene"
    bl_label = "Start Photogrammetry"
    bl_description = "Starts the photogrammetry process"

    def execute(self, context):
        wm = context.window_manager
        settings = context.scene.oneshot_settings
        prefs = context.preferences.addons[__package__].preferences

        colmap_executable_path = prefs.colmap_executable_path
        image_input_folder = settings.image_input_folder
        delete_workspace = settings.delete_workspace
        reconstruction_output_folder = settings.reconstruction_output_folder

        if not all([image_input_folder, colmap_executable_path, reconstruction_output_folder]):
            self.report({'ERROR'}, "One or more paths are not set.")
            return {'CANCELLED'}
        
        workspace_path = Path(reconstruction_output_folder)
        workspace_path.mkdir(parents=True, exist_ok=True)

        wm.oneshot_progress = "Starting background process..."

        thread = threading.Thread(
            target=run_photogrammetry_process,
            args=(
                context,
                settings,
                colmap_executable_path,
                str(image_input_folder),
                workspace_path,
                delete_workspace
            )
        )
        thread.start()

        global _background_thread
        _background_thread = thread

        return bpy.ops.oneshot.reconstruct_monitor('INVOKE_DEFAULT')

class ONESHOT_OT_reconstruct_monitor(bpy.types.Operator):
    bl_idname = "oneshot.reconstruct_monitor"
    bl_label = "Monitor Photogrammetry"

    _timer = None
    _thread = None

    def invoke(self, context, event):
        global _background_thread
        self._thread = _background_thread

        if not self._thread or not self._thread.is_alive():
            self.report({'INFO'}, "Photogrammetry process not running.")
            return {'FINISHED'}

        self._timer = context.window_manager.event_timer_add(0.1, window=context.window)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type == 'TIMER':
            if not self._thread.is_alive():
                context.window_manager.event_timer_remove(self._timer)
                global _background_thread
                _background_thread = None
                return {'FINISHED'}
            else:
                context.area.tag_redraw()
        return {'PASS_THROUGH'}

    def cancel(self, context):
        context.window_manager.event_timer_remove(self._timer)

class ONESHOT_OT_import_colmap_model(bpy.types.Operator):
    bl_idname = "oneshot.import_colmap_model"
    bl_label = "Import COLMAP Model"
    bl_description = "Directly import a COLMAP model"

    def execute(self, context):
        settings = context.scene.oneshot_settings
        
        model_path = settings.colmap_model_path
        if not model_path or not os.path.isdir(model_path):
            self.report({'ERROR'}, "COLMAP model path is not valid.")
            return {'CANCELLED'}

        success = import_colmap_scene(
            reconstruction_dir_path=model_path,
            import_cameras=settings.import_cameras,
            add_background_image=settings.add_background_image_for_each_camera,
            add_camera_motion=settings.add_camera_motion_as_animation,
            import_points=settings.import_points,
            add_points_as_mesh_object=settings.add_points_as_mesh_object
        )

        if success:
            self.report({'INFO'}, "COLMAP model imported successfully.")
        else:
            self.report({'ERROR'}, "Failed to import COLMAP model.")

        return {'FINISHED'}
