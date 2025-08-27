import bpy
import threading
import time
import subprocess
import os
import shutil
from pathlib import Path
from .importer import import_colmap_scene

_background_thread = None

def _extract_frames(video_path: str, output_dir: str, image_format: str) -> bool:
    temp_scene = None
    original_scene = bpy.context.window.scene # Store original scene
    try:
        print(f"oneShot: _extract_frames: Starting frame extraction for video: {video_path} to output directory: {output_dir}")
        # Create a new, temporary scene
        temp_scene = bpy.data.scenes.new("Frame Extraction Scene")
        print(f"oneShot: _extract_frames: Created temporary scene: {temp_scene.name}")
        
        # Make the new scene active for operations
        bpy.context.window.scene = temp_scene
        print(f"oneShot: _extract_frames: Set active scene to: {temp_scene.name}")

        # Ensure sequence editor exists
        if not temp_scene.sequence_editor:
            temp_scene.sequence_editor_create()
            print("oneShot: _extract_frames: Sequence editor created for temporary scene.")
        else:
            print("oneShot: _extract_frames: Sequence editor already exists for temporary scene.")

        # Add the video as a movie strip
        bpy.ops.sequencer.movie_strip_add(filepath=video_path, frame_start=1)
        print(f"oneShot: _extract_frames: Added movie strip from {video_path}.")

        # Get a reference to the newly created video strip
        movie_strip = None
        for strip in temp_scene.sequence_editor.sequences:
            if strip.type == 'MOVIE' and strip.filepath == video_path:
                movie_strip = strip
                break
        
        if not movie_strip:
            print(f"oneShot: _extract_frames Error: Could not find movie strip for {video_path}")
            return False
        print(f"oneShot: _extract_frames: Found movie strip: {movie_strip.name}")

        # Set the temporary scene's frame_end to match the video strip's duration
        temp_scene.frame_end = movie_strip.frame_final_duration
        print(f"oneShot: _extract_frames: Set scene frame_end to: {temp_scene.frame_end}")

        # Configure the scene's render settings
        temp_scene.render.filepath = output_dir
        temp_scene.render.image_settings.file_format = image_format
        temp_scene.render.image_settings.color_mode = 'RGB'
        print(f"oneShot: _extract_frames: Configured render settings: filepath={output_dir}, format={image_format}, color_mode=RGB")

        # Run the animation render
        print("oneShot: _extract_frames: Starting animation render...")
        bpy.ops.render.render(animation=True, scene=temp_scene.name)
        print("oneShot: _extract_frames: Animation render complete.")

        print("oneShot: _extract_frames: Frame extraction successful.")
        return True

    except Exception as e:
        print(f"oneShot: _extract_frames Error: An error occurred during frame extraction: {e}")
        return False
    finally:
        print("oneShot: _extract_frames: Entering finally block for cleanup.")
        # Restore original scene context
        if temp_scene and original_scene:
            bpy.context.window.scene = original_scene
            print(f"oneShot: _extract_frames: Restored original scene: {original_scene.name}")
        
        # Ensure the temporary scene is deleted
        if temp_scene and temp_scene.name in bpy.data.scenes:
            print(f"oneShot: _extract_frames: Deleting temporary scene: {temp_scene.name}")
            bpy.data.scenes.remove(temp_scene)
            print("oneShot: _extract_frames: Temporary scene deleted.")

def _run_colmap(colmap_executable_path: str, image_directory: str, workspace_path: Path) -> Path | None:
    try:
        print(f"oneShot: _run_colmap: Starting COLMAP execution. Executable: {colmap_executable_path}, Images: {image_directory}, Workspace: {workspace_path})")
        database_path = workspace_path / "database.db"
        output_path = workspace_path / "output"
        output_path.mkdir(parents=True, exist_ok=True)

        commands = [
            [colmap_executable_path, "feature_extractor", "--database_path", str(database_path), "--image_path", str(image_directory), "--ImageReader.single_camera", "1"],
            [colmap_executable_path, "sequential_matcher", "--database_path", str(database_path)], # Changed from exhaustive_matcher
            [colmap_executable_path, "mapper", "--database_path", str(database_path), "--image_path", str(image_directory), "--output_path", str(output_path)],
        ]

        for cmd in commands:
            print(f"oneShot: _run_colmap: Running COLMAP command: {' '.join(cmd)}")
            process = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"oneShot: _run_colmap STDOUT:\n{process.stdout}")
            print(f"oneShot: _run_colmap STDERR:\n{process.stderr}")
        
        print("oneShot: _run_colmap: COLMAP execution successful.")
        
        # Return the path to the sparse reconstruction directory
        sparse_reconstruction_path = output_path / "sparse" / "0"
        if sparse_reconstruction_path.exists():
            print(f"oneShot: _run_colmap: Sparse reconstruction found at: {sparse_reconstruction_path}")
            return sparse_reconstruction_path
        else:
            print(f"oneShot: _run_colmap Error: Sparse reconstruction directory not found at: {sparse_reconstruction_path}")
            return None

    except subprocess.CalledProcessError as e:
        print(f"oneShot: _run_colmap Error: COLMAP command failed: {e}")
        print(f"oneShot: _run_colmap STDOUT:\n{e.stdout}")
        print(f"oneShot: _run_colmap STDERR:\n{e.stderr}")
        return None
    except Exception as e:
        print(f"oneShot: _run_colmap Error: An error occurred during COLMAP execution: {e}")
        return None

def run_photogrammetry_process(colmap_exe_path: str, image_dir: str, workspace_dir: Path, delete_workspace: bool):
    # wm = context.window_manager  <-- Removed
    # settings = context.scene.oneshot_settings <-- Removed
    # prefs = context.preferences.addons[__package__].preferences <-- Removed
    
    # Progress updates will be handled by the main thread via the modal operator
    # This function should not directly access Blender's context or UI properties.

    try:
        print("oneShot: run_photogrammetry_process: Starting background photogrammetry process.")
        
        # Step 2/3: Running COLMAP Reconstruction...
        # Progress update will be done by the main thread
        print("oneShot: run_photogrammetry_process: Calling _run_colmap...")
        sparse_reconstruction_path = _run_colmap(colmap_exe_path, image_dir, workspace_dir)
        if sparse_reconstruction_path is None:
            print("oneShot: run_photogrammetry_process Error: COLMAP reconstruction failed.")
            return # Indicate failure to the main thread

        print("oneShot: run_photogrammetry_process: COLMAP reconstruction completed successfully.")

        # Step 3/3: Importing Scene into Blender...
        # Progress update will be done by the main thread
        print("oneShot: run_photogrammetry_process: Calling import_colmap_scene...")
        if not import_colmap_scene(str(sparse_reconstruction_path)):
            print("oneShot: run_photogrammetry_process Error: Scene import failed.")
            return # Indicate failure to the main thread
        print("oneShot: run_photogrammetry_process: Scene imported successfully.")

        print("oneShot: run_photogrammetry_process: Photogrammetry process finished.")

    except Exception as e:
        print(f"oneShot: run_photogrammetry_process Error: An unexpected error occurred: {e}")
    finally:
        print("oneShot: run_photogrammetry_process: Entering finally block for cleanup.")
        if workspace_dir and workspace_dir.exists():
            if delete_workspace:
                shutil.rmtree(workspace_dir)
                print(f"oneShot: run_photogrammetry_process: Cleaned up temporary workspace: {workspace_dir}")
            else:
                print(f"oneShot: run_photogrammetry_process: Temporary workspace retained: {workspace_dir}")
        else:
            print("oneShot: run_photogrammetry_process: No temporary workspace to clean up or retain.")

class ONESHOT_OT_extract_frames(bpy.types.Operator):
    bl_idname = "oneshot.extract_frames"
    bl_label = "Extract Frames"
    bl_description = "Extracts frames from the video to the specified folder using FFmpeg"

    def execute(self, context):
        wm = context.window_manager
        settings = context.scene.oneshot_settings
        prefs = context.preferences.addons[__package__].preferences

        video_input_path = settings.video_input_path
        image_output_folder = settings.image_output_folder
        ffmpeg_executable_path = prefs.ffmpeg_executable_path
        image_format = settings.image_format.lower() # png or jpg

        # --- Validation ---
        if not video_input_path or not os.path.exists(video_input_path):
            self.report({'ERROR'}, "Video input path not set or invalid.")
            return {'CANCELLED'}
        
        if not image_output_folder:
            self.report({'ERROR'}, "Image output folder not set.")
            return {'CANCELLED'}
        
        if not os.path.exists(image_output_folder):
            try:
                os.makedirs(image_output_folder)
            except OSError as e:
                self.report({'ERROR'}, f"Could not create output directory: {e}")
                return {'CANCELLED'}

        if not ffmpeg_executable_path or not os.path.exists(ffmpeg_executable_path):
            self.report({'ERROR'}, "FFmpeg executable path not set or invalid. Please configure in addon preferences.")
            return {'CANCELLED'}

        # --- FFmpeg Command ---
        # Example: ffmpeg -i input.mp4 output_folder/%04d.png
        output_pattern = os.path.join(image_output_folder, f"%04d.{image_format}")
        command = [
            ffmpeg_executable_path,
            "-i", video_input_path,
            output_pattern
        ]

        wm.oneshot_progress = "Extracting frames with FFmpeg..."
        print(f"oneShot: Running FFmpeg command: {' '.join(command)}")

        try:
            process = subprocess.run(command, capture_output=True, text=True, check=True)
            print(f"oneShot: FFmpeg STDOUT:\n{process.stdout}")
            print(f"oneShot: FFmpeg STDERR:\n{process.stderr}")
            self.report({'INFO'}, "Frame extraction successful!")
            wm.oneshot_progress = "Frame extraction complete."
            return {'FINISHED'}
        except subprocess.CalledProcessError as e:
            self.report({'ERROR'}, f"FFmpeg command failed: {e.stderr}")
            wm.oneshot_progress = "Error: Frame extraction failed."
            print(f"oneShot: FFmpeg Error: {e.stderr}")
            return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"An unexpected error occurred during FFmpeg execution: {e}")
            wm.oneshot_progress = "Error: Frame extraction failed."
            print(f"oneShot: Unexpected FFmpeg Error: {e}")
            return {'CANCELLED'}

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

        # --- Pre-flight checks and setup ---
        if not image_input_folder or not os.path.exists(image_input_folder):
            wm.oneshot_progress = "Error: Image input folder not set or invalid."
            print(f"oneShot: ONESHOT_OT_reconstruct_scene Error: Image input folder invalid: {image_input_folder}")
            return {'CANCELLED'}
        
        if not colmap_executable_path or not os.path.exists(colmap_executable_path):
            wm.oneshot_progress = "Error: COLMAP executable path not set or invalid."
            print(f"oneShot: ONESHOT_OT_reconstruct_scene Error: COLMAP executable path invalid: {colmap_executable_path}")
            return {'CANCELLED'}

        job_id = int(time.time())
        temp_workspace_root = Path(bpy.app.tempdir) / f"oneshot_job_{job_id}"
        temp_workspace_root.mkdir(parents=True, exist_ok=True)
        print(f"oneShot: ONESHOT_OT_reconstruct_scene: Created temporary workspace: {temp_workspace_root}")

        # --- Create and start background thread for COLMAP and import ---
        wm.oneshot_progress = "Starting background process..."
        print("oneShot: ONESHOT_OT_reconstruct_scene: Operator executed. Starting thread.")

        thread = threading.Thread(
            target=run_photogrammetry_process,
            args=(
                colmap_executable_path,
                str(image_input_folder),
                temp_workspace_root,
                delete_workspace
            )
        )
        thread.start()

        global _background_thread
        _background_thread = thread

        # Invoke the modal operator to monitor the thread
        return bpy.ops.oneshot.reconstruct_monitor('INVOKE_DEFAULT')

class ONESHOT_OT_reconstruct_monitor(bpy.types.Operator):
    bl_idname = "oneshot.reconstruct_monitor"
    bl_label = "Monitor Photogrammetry"

    _timer = None
    _thread = None

    def invoke(self, context, event):
        wm = context.window_manager
        global _background_thread
        self._thread = _background_thread

        if not self._thread or not self._thread.is_alive():
            self.report({'INFO'}, "Photogrammetry process not running.")
            print("oneShot: ONESHOT_OT_monitor_photogrammetry: Process not running or thread not found.")
            return {'FINISHED'}

        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        print("oneShot: ONESHOT_OT_monitor_photogrammetry: Monitoring started.")
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type == 'TIMER':
            if not self._thread.is_alive():
                self.report({'INFO'}, "Photogrammetry process finished.")
                context.window_manager.event_timer_remove(self._timer)
                _background_thread = None
                print("oneShot: ONESHOT_OT_monitor_photogrammetry: Process finished, monitoring stopped.")
                return {'FINISHED'}
            else:
                # Force UI redraw to update progress text
                context.area.tag_redraw()
        return {'PASS_THROUGH'}

    def cancel(self, context):
        context.window_manager.event_timer_remove(self._timer)
        self.report({'INFO'}, "Photogrammetry monitoring cancelled.")
        print("oneShot: ONESHOT_OT_monitor_photogrammetry: Monitoring cancelled.")
        if hasattr(context.window_manager, 'oneshot_photogrammetry_thread'):
            _background_thread = None
            print("oneShot: ONESHOT_OT_monitor_photogrammetry: Thread reference cleared.") # type: ignore