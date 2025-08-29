import bpy
import threading
import time
import subprocess
import os
import shutil
from pathlib import Path
from .importer import import_colmap_scene
import datetime
import mathutils
import math

_background_thread = None
_current_process = None
_process_terminated_by_user = False
_video_resolution = None # Global variable to store video resolution

def run_photogrammetry_process(context, settings, is_video: bool):
    global _current_process, _process_terminated_by_user
    _process_terminated_by_user = False # Reset flag for each new run

    # Get video resolution using ffprobe
    global _video_resolution
    _video_resolution = None # Reset for each new run
    if is_video:
        try:
            ffmpeg_path = context.preferences.addons[__package__].preferences.ffmpeg_executable_path
            # Derive ffprobe_path from ffmpeg_path
            ffprobe_path = str(Path(ffmpeg_path).parent / "ffprobe.exe")
            ffprobe_command = [
                ffprobe_path, # Use the correct ffprobe_path here
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height",
                "-of", "csv=s=x:p=0",
                settings.input_path
            ]
            ffprobe_output = subprocess.check_output(ffprobe_command, universal_newlines=True).strip()
            width, height = map(int, ffprobe_output.split('x'))
            _video_resolution = (width, height)
            print(f"oneShot: Detected video resolution: {width}x{height}")
        except Exception as e:
            print(f"oneShot: Error getting video resolution with ffprobe: {e}")
            _video_resolution = None # Reset in case of error

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

        print("oneShot: Starting COLMAP Feature Extraction process...") # NEW LINE
        context.window_manager.oneshot_progress = "Step 2/4: Running COLMAP Feature Extraction..."
        colmap_exe_path = context.preferences.addons[__package__].preferences.colmap_executable_path
        database_path = output_path / "database.db"
        
        # Feature Extractor
        cmd = [colmap_exe_path, "feature_extractor", "--database_path", str(database_path), "--image_path", str(images_path), "--ImageReader.single_camera", "1", "--SiftExtraction.use_gpu", "1"]
        
        print(f"oneShot: Running COLMAP feature_extractor command: {' '.join(cmd)}") # More specific
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
        _current_process = process # Assign to global
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                context.window_manager.oneshot_progress_detail = output.strip()
        print("oneShot: COLMAP feature_extractor process finished.") # NEW
        if process.poll() != 0:
            if _process_terminated_by_user:
                context.window_manager.oneshot_progress = "Process stopped by user."
                print("oneShot: COLMAP feature_extractor stopped by user.")
            else:
                context.window_manager.oneshot_progress = "Error: COLMAP feature_extractor failed."
                print("oneShot: COLMAP feature_extractor failed. Check console for details.") # More specific
            return
        print("oneShot: COLMAP feature_extractor completed successfully.") # NEW

        print("oneShot: Starting COLMAP Sequential Matcher process...") # NEW LINE
        context.window_manager.oneshot_progress = "Step 3/4: Running COLMAP Sequential Matcher..."
        # Sequential Matcher
        cmd = [colmap_exe_path, "sequential_matcher", "--database_path", str(database_path)]
        print(f"oneShot: Running COLMAP sequential_matcher command: {' '.join(cmd)}") # More specific
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
        _current_process = process # Assign to global
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                context.window_manager.oneshot_progress_detail = output.strip()
        print("oneShot: COLMAP sequential_matcher process finished.") # NEW
        if process.poll() != 0:
            if _process_terminated_by_user:
                context.window_manager.oneshot_progress = "Process stopped by user."
                print("oneShot: COLMAP sequential_matcher stopped by user.")
            else:
                context.window_manager.oneshot_progress = "Error: COLMAP sequential_matcher failed."
                print("oneShot: COLMAP sequential_matcher failed. Check console for details.") # More specific
            return
        print("oneShot: COLMAP sequential_matcher completed successfully.") # NEW

        print("oneShot: Starting COLMAP Mapper process...") # NEW LINE
        context.window_manager.oneshot_progress = "Step 4/4: Running COLMAP Mapper..."
        # Mapper
        cmd = [colmap_exe_path, "mapper", "--database_path", str(database_path), "--image_path", str(images_path), "--output_path", str(sparse_path)]
        print(f"oneShot: Running COLMAP mapper command: {' '.join(cmd)}") # More specific
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
        _current_process = process # Assign to global
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                context.window_manager.oneshot_progress_detail = output.strip()
        print("oneShot: COLMAP mapper process finished.") # NEW
        if process.poll() != 0:
            if _process_terminated_by_user:
                context.window_manager.oneshot_progress = "Process stopped by user."
                print("oneShot: COLMAP mapper stopped by user.")
            else:
                context.window_manager.oneshot_progress = "Error: COLMAP mapper failed."
                print("oneShot: COLMAP mapper failed. Check console for details.") # More specific
            return
        print("oneShot: COLMAP mapper completed successfully.") # NEW

        print("oneShot: Starting COLMAP Model Converter process...") # NEW LINE
        # Model Converter
        context.window_manager.oneshot_progress = "Converting model..."
        print("oneShot: Converting model to TXT...")
        model_path_in = sparse_path / "0"
        if model_path_in.exists():
            cmd = [colmap_exe_path, "model_converter", "--input_path", str(model_path_in), "--output_path", str(sparse_path), "--output_type", "TXT"]
            print(f"oneShot: Running COLMAP model_converter command: {' '.join(cmd)}") # More specific
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
            _current_process = process # Assign to global
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    context.window_manager.oneshot_progress_detail = output.strip()
            print("oneShot: COLMAP model_converter process finished.") # NEW
            if process.poll() != 0:
                if _process_terminated_by_user:
                    context.window_manager.oneshot_progress = "Process stopped by user."
                    print("oneShot: COLMAP model_converter stopped by user.")
                else:
                    context.window_manager.oneshot_progress = "Error: COLMAP model_converter failed."
                    print("oneShot: COLMAP model_converter failed. Check console for details.") # More specific
                return
            print("oneShot: COLMAP model_converter completed successfully.") # NEW
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

                # Apply video resolution if available
                global _video_resolution
                if _video_resolution:
                    bpy.context.scene.render.resolution_x = _video_resolution[0]
                    bpy.context.scene.render.resolution_y = _video_resolution[1]
                    print(f"oneShot: Applied render resolution: {_video_resolution[0]}x{_video_resolution[1]}")
                    _video_resolution = None # Clear after use

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
            self.report({'INFO'}, "No photogrammetry process is currently currently running.")
        return {'FINISHED'}


class ONESHOT_OT_optimise_scene(bpy.types.Operator):
    bl_idname = "oneshot.optimise_scene"
    bl_label = "Optimise Scene"
    bl_description = "Optimises the imported scene for better viewing"

    def execute(self, context):
        # 0. Video Proxy Generation
        print("oneShot: Starting video proxy generation...")
        if "Animated Camera" in bpy.data.objects:
            animated_camera = bpy.data.objects["Animated Camera"]
            if animated_camera.data and animated_camera.data.background_images:
                for bg_img in animated_camera.data.background_images:
                    if bg_img.source == 'MOVIE' and bg_img.clip:
                        original_video_path = bpy.path.abspath(bg_img.clip.filepath)
                        print(f"oneShot: Original video path: {original_video_path}")
                        if os.path.exists(original_video_path):
                            video_dir = Path(original_video_path).parent
                            proxy_dir = video_dir / "proxy"
                            proxy_dir.mkdir(parents=True, exist_ok=True)
                            print(f"oneShot: Proxy directory created: {proxy_dir}")
                            
                            video_name = Path(original_video_path).stem
                            proxy_video_path = proxy_dir / f"{video_name}_proxy.mp4"
                            print(f"oneShot: Proxy video output path: {proxy_video_path}")

                            ffmpeg_path = context.preferences.addons[__package__].preferences.ffmpeg_executable_path
                            print(f"oneShot: FFmpeg executable path: {ffmpeg_path}")
                            
                            command = [
                                ffmpeg_path,
                                "-i", original_video_path,
                                "-vf", "scale=iw/2:ih/2",
                                "-c:v", "libx264",
                                "-crf", "23",
                                "-preset", "medium",
                                "-y", # Overwrite output file without asking
                                str(proxy_video_path)
                            ]
                            print(f"oneShot: Running FFmpeg proxy command: {' '.join(command)}")
                            try:
                                subprocess.run(command, check=True, capture_output=True, text=True)
                                print(f"oneShot: Video proxy generated successfully: {proxy_video_path}")
                                bg_img.clip.filepath = str(proxy_video_path)
                                print(f"oneShot: Updated Animated Camera movie clip filepath to: {bg_img.clip.filepath}")
                                self.report({'INFO'}, f"Generated and applied video proxy: {proxy_video_path}")
                            except subprocess.CalledProcessError as e:
                                self.report({'ERROR'}, f"FFmpeg proxy generation failed: {e.stderr}")
                                print(f"oneShot: FFmpeg proxy generation failed. Stderr: {e.stderr}")
                                print(f"oneShot: FFmpeg proxy generation failed. Stdout: {e.stdout}")
                            except Exception as e:
                                self.report({'ERROR'}, f"Error during proxy generation: {e}")
                                print(f"oneShot: Error during proxy generation: {e}")
                        else:
                            self.report({'WARNING'}, f"Original video not found: {original_video_path}")
                            print(f"oneShot: Warning: Original video not found at {original_video_path}. Skipping proxy generation.")
            else:
                self.report({'WARNING'}, "'Animated Camera' has no background movie clip.")
                print("oneShot: Warning: 'Animated Camera' has no background movie clip. Skipping proxy generation.")
        else:
            self.report({'WARNING'}, "'Animated Camera' object not found for proxy generation.")
            print("oneShot: Warning: 'Animated Camera' object not found. Skipping proxy generation.")
        print("oneShot: Video proxy generation finished.")

        # 1. Find the "Cameras" collection and hide it from the viewport.
        print("oneShot: Hiding 'Cameras' collection...")
        if "Cameras" in bpy.data.collections:
            cameras_collection = bpy.data.collections["Cameras"]
            cameras_collection.hide_viewport = True
            self.report({'INFO'}, "Hid 'Cameras' collection.")
            print("oneShot: 'Cameras' collection hidden.")
        else:
            self.report({'WARNING'}, "'Cameras' collection not found.")
            print("oneShot: Warning: 'Cameras' collection not found.")

        # 2. Find the "Animated Camera" object and set it as the active scene camera.
        print("oneShot: Setting 'Animated Camera' as active scene camera...")
        if "Animated Camera" in bpy.data.objects:
            animated_camera = bpy.data.objects["Animated Camera"]
            context.scene.camera = animated_camera
            self.report({'INFO'}, "Set 'Animated Camera' as active scene camera.")
            print("oneShot: 'Animated Camera' set as active scene camera.")
        else:
            self.report({'WARNING'}, "'Animated Camera' object not found.")
            print("oneShot: Warning: 'Animated Camera' object not found. Cannot set as active camera.")

        # 3. Precise Re-orientation of "Reconstruction Collection"
        print("oneShot: Starting precise re-orientation...")
        if "Reconstruction Collection" in bpy.data.collections and "frame_000000_cam" in bpy.data.objects:
            reconstruction_collection = bpy.data.collections["Reconstruction Collection"]
            frame_000000_cam = bpy.data.objects["frame_000000_cam"]
            print(f"oneShot: Found 'Reconstruction Collection' and 'frame_000000_cam'.")

            # Set 3D cursor to world origin
            context.scene.cursor.location = (0, 0, 0)
            print("oneShot: 3D cursor set to world origin (0,0,0).")

            # Get current world rotation of frame_000000_cam
            current_rot_euler = frame_000000_cam.matrix_world.to_euler('XYZ')
            print(f"oneShot: Current 'frame_000000_cam' rotation (Euler XYZ): {current_rot_euler}")

            # Target rotation: (90, 0, Z)
            target_rot_euler = mathutils.Euler((math.radians(90), 0, current_rot_euler.z), 'XYZ')
            print(f"oneShot: Target rotation (Euler XYZ): {target_rot_euler} (Z preserved from current)")

            # Calculate corrective rotation matrix
            corrective_matrix = target_rot_euler.to_matrix().to_4x4() @ current_rot_euler.to_matrix().inverted().to_4x4()
            print(f"oneShot: Corrective rotation matrix calculated.")

            # Create an empty object to act as the parent for the collection if it doesn't have one
            collection_parent_name = "Reconstruction_Collection_Parent"
            collection_parent = None
            if collection_parent_name not in bpy.data.objects:
                bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
                collection_parent = context.active_object
                collection_parent.name = collection_parent_name
                print(f"oneShot: Created new parent empty: {collection_parent_name}")
            else:
                collection_parent = bpy.data.objects[collection_parent_name]
                print(f"oneShot: Found existing parent empty: {collection_parent_name}")

            # Parent all objects in the "Reconstruction Collection" to this empty
            objects_to_parent = [obj for obj in reconstruction_collection.objects if obj.parent is None]
            print(f"oneShot: Found {len(objects_to_parent)} objects in 'Reconstruction Collection' to parent.")

            for obj in objects_to_parent:
                if reconstruction_collection.name in obj.users_collection:
                    obj.users_collection.remove(reconstruction_collection)
                    print(f"oneShot: Unlinked {obj.name} from 'Reconstruction Collection'.")
                if bpy.context.scene.collection.name not in obj.users_collection:
                    bpy.context.scene.collection.objects.link(obj)
                    print(f"oneShot: Linked {obj.name} to scene collection.")
            
            for obj in objects_to_parent:
                obj.parent = collection_parent
                obj.matrix_parent_inverse = collection_parent.matrix_world.inverted()
                print(f"oneShot: Parented {obj.name} to {collection_parent.name}.")
            print("oneShot: All relevant objects in 'Reconstruction Collection' parented to empty.")

            # Apply the corrective rotation to the parent empty
            collection_parent.matrix_world = corrective_matrix @ collection_parent.matrix_world
            print(f"oneShot: Applied corrective rotation to parent empty '{collection_parent.name}'.")
            
            self.report({'INFO'}, "Re-oriented 'Reconstruction Collection' precisely.")
        else:
            self.report({'WARNING'}, "'Reconstruction Collection' or 'frame_000000_cam' not found. Skipping precise re-orientation.")
            print("oneShot: Warning: 'Reconstruction Collection' or 'frame_000000_cam' not found. Skipping precise re-orientation.")
        print("oneShot: Precise re-orientation finished.")

        return {'FINISHED'} # type: ignore