import bpy
import threading
import time
import subprocess
import os
import shutil
from pathlib import Path
from .importer import import_colmap_scene
import datetime

_background_thread = None
_current_process = None
_process_terminated_by_user = False

def run_photogrammetry_process(context, settings, is_video: bool):
    global _current_process, _process_terminated_by_user
    _process_terminated_by_user = False # Reset flag for each new run

    try:
        print("oneShot: Starting photogrammetry process...")
        
        # Get the base output path from settings
        base_output_path = Path(settings.output_path)

        # Determine the project directory name based on the input video file or image sequence folder
        project_dir_name = ""
        if is_video:
            video_file_name = os.path.basename(settings.input_path)
            project_dir_name = os.path.splitext(video_file_name)[0]
        else:
            # If it's an image sequence, use the input directory name as the project name
            project_dir_name = os.path.basename(settings.input_path)
            if not project_dir_name: # Fallback if input_path is just a drive letter or root
                project_dir_name = f"colmapFile-{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Create the new project-specific output path
        project_output_path = base_output_path / project_dir_name
        project_output_path.mkdir(parents=True, exist_ok=True)

        # Update all subsequent paths to be relative to the new project_output_path
        output_path = project_output_path # This is the new effective output_path
        images_path = output_path / "images"
        sparse_path = output_path / "sparse"
        
        print(f"oneShot: Creating directories: {images_path} and {sparse_path}")
        images_path.mkdir(parents=True, exist_ok=True)
        sparse_path.mkdir(parents=True, exist_ok=True)

        if is_video:
            context.window_manager.oneshot_progress = "Step 1/4: Extracting Frames..."
            print("oneShot: Input is a video, starting frame extraction.")
            ffmpeg_path = context.preferences.addons[__package__].preferences.ffmpeg_executable_path
            output_pattern = os.path.join(images_path, "frame_%06d.jpg")
            command = [ffmpeg_path, "-i", settings.input_path, "-q:v", "1", "-start_number", "0", output_pattern]
            print(f"oneShot: Running FFmpeg command: {' '.join(command)}")
            
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
            _current_process = process # Assign to global
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    context.window_manager.oneshot_progress_detail = output.strip()
            if process.poll() != 0:
                if _process_terminated_by_user:
                    context.window_manager.oneshot_progress = "Process stopped by user."
                    print("oneShot: Frame extraction stopped by user.")
                else:
                    context.window_manager.oneshot_progress = "Error: Frame extraction failed."
                    print("oneShot: Frame extraction failed.")
                return
            print("oneShot: Frame extraction complete.")
        else:
            print("oneShot: Input is an image sequence. Copying files...")
            for item in os.listdir(settings.input_path):
                s = os.path.join(settings.input_path, item)
                d = os.path.join(images_path, item)
                if os.path.isfile(s):
                    shutil.copy2(s, d)
            print("oneShot: Image copy complete.")

        context.window_manager.oneshot_progress = "Step 2/4: Running COLMAP Feature Extraction..."
        colmap_exe_path = context.preferences.addons[__package__].preferences.colmap_executable_path
        database_path = output_path / "database.db"
        
        # Feature Extractor
        cmd = [colmap_exe_path, "feature_extractor", "--database_path", str(database_path), "--image_path", str(images_path), "--ImageReader.single_camera", "1", "--SiftExtraction.use_gpu", "1"]
        print(f"oneShot: Running COLMAP command: {' '.join(cmd)}")
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
        _current_process = process # Assign to global
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                context.window_manager.oneshot_progress_detail = output.strip()
        if process.poll() != 0:
            if _process_terminated_by_user:
                context.window_manager.oneshot_progress = "Process stopped by user."
                print("oneShot: COLMAP feature_extractor stopped by user.")
            else:
                context.window_manager.oneshot_progress = "Error: COLMAP feature_extractor failed."
                print("oneShot: COLMAP feature_extractor failed.")
            return

        context.window_manager.oneshot_progress = "Step 3/4: Running COLMAP Sequential Matcher..."
        # Sequential Matcher
        cmd = [colmap_exe_path, "sequential_matcher", "--database_path", str(database_path)]
        print(f"oneShot: Running COLMAP command: {' '.join(cmd)}")
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
        _current_process = process # Assign to global
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                context.window_manager.oneshot_progress_detail = output.strip()
        if process.poll() != 0:
            if _process_terminated_by_user:
                context.window_manager.oneshot_progress = "Process stopped by user."
                print("oneShot: COLMAP sequential_matcher stopped by user.")
            else:
                context.window_manager.oneshot_progress = "Error: COLMAP sequential_matcher failed."
                print("oneShot: COLMAP sequential_matcher failed.")
            return

        context.window_manager.oneshot_progress = "Step 4/4: Running COLMAP Mapper..."
        # Mapper
        cmd = [colmap_exe_path, "mapper", "--database_path", str(database_path), "--image_path", str(images_path), "--output_path", str(sparse_path)]
        print(f"oneShot: Running COLMAP command: {' '.join(cmd)}")
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
        _current_process = process # Assign to global
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                context.window_manager.oneshot_progress_detail = output.strip()
        if process.poll() != 0:
            if _process_terminated_by_user:
                context.window_manager.oneshot_progress = "Process stopped by user."
                print("oneShot: COLMAP mapper stopped by user.")
            else:
                context.window_manager.oneshot_progress = "Error: COLMAP mapper failed."
                print("oneShot: COLMAP mapper failed.")
            return

        # Model Converter
        context.window_manager.oneshot_progress = "Converting model..."
        print("oneShot: Converting model to TXT...")
        model_path_in = sparse_path / "0"
        if model_path_in.exists():
            cmd = [colmap_exe_path, "model_converter", "--input_path", str(model_path_in), "--output_path", str(sparse_path), "--output_type", "TXT"]
            print(f"oneShot: Running COLMAP command: {' '.join(cmd)}")
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
            _current_process = process # Assign to global
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    context.window_manager.oneshot_progress_detail = output.strip()
            if process.poll() != 0:
                if _process_terminated_by_user:
                    context.window_manager.oneshot_progress = "Process stopped by user."
                    print("oneShot: COLMAP model_converter stopped by user.")
                else:
                    context.window_manager.oneshot_progress = "Error: COLMAP model_converter failed."
                    print("oneShot: COLMAP model_converter failed.")
                return
        else:
            print("oneShot: No sparse model to convert.")

        context.window_manager.oneshot_progress = "Importing Scene..."
        reconstruction_path = sparse_path / "0"
        if not reconstruction_path.exists():
            context.window_manager.oneshot_progress = "Error: Reconstruction failed, model not found."
            return

        if not import_colmap_scene(reconstruction_folder_path=str(reconstruction_path), settings=settings):
            context.window_manager.oneshot_progress = "Error: Scene import failed."
            return
        
        context.window_manager.oneshot_progress = "Success! Scene Imported."

    except Exception as e:
        context.window_manager.oneshot_progress = f"Error: {e}"
        print(f"oneShot: An unexpected error occurred: {e}")
    finally:
        _current_process = None # Clear global process reference
        _process_terminated_by_user = False # Reset flag

class ONESHOT_OT_reconstruct_scene(bpy.types.Operator):
    bl_idname = "oneshot.reconstruct_scene"
    bl_label = "Generate Scene"
    bl_description = "Starts the photogrammetry process"

    def execute(self, context):
        settings = context.scene.oneshot_settings
        input_path = settings.input_path

        if not input_path or not settings.output_path:
            self.report({'ERROR'}, "Input and Output paths must be set.")
            return {'CANCELLED'}

        is_video = os.path.isfile(input_path)
        
        thread = threading.Thread(target=run_photogrammetry_process, args=(context, settings, is_video))
        thread.start()

        global _background_thread
        _background_thread = thread

        return bpy.ops.oneshot.reconstruct_monitor('INVOKE_DEFAULT')

class ONESHOT_OT_reconstruct_monitor(bpy.types.Operator):
    bl_idname = "oneshot.reconstruct_monitor"
    bl_label = "Monitor Scene Generation"

    _timer = None
    _thread = None

    def invoke(self, context, event):
        global _background_thread
        self._thread = _background_thread

        if not self._thread or not self._thread.is_alive():
            self.report({'INFO'}, "Process not running.")
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

        success = import_colmap_scene(reconstruction_folder_path=model_path, settings=settings)

        if success:
            self.report({'INFO'}, "COLMAP model imported successfully.")
        else:
            self.report({'ERROR'}, "Failed to import COLMAP model.")

        return {'FINISHED'}


class ONESHOT_OT_stop_process(bpy.types.Operator):
    bl_idname = "oneshot.stop_process"
    bl_label = "Stop Process"
    bl_description = "Stops the current photogrammetry process"

    def execute(self, context):
        global _current_process, _process_terminated_by_user
        if _current_process and _current_process.poll() is None: # Check if process is running
            _process_terminated_by_user = True
            _current_process.terminate() # Request graceful termination
            self.report({'INFO'}, "Photogrammetry process termination requested.")
        else:
            self.report({'INFO'}, "No photogrammetry process is currently running.")
        return {'FINISHED'}