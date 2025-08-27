import bpy

def extract_frames(video_path: str, output_dir: str) -> bool:
    print(f"oneShot: Starting frame extraction for video: {video_path} to output directory: {output_dir}")
    temp_scene = None
    try:
        # Create a new, temporary scene
        temp_scene = bpy.data.scenes.new("Frame Extraction Scene")
        print(f"oneShot: Created temporary scene: {temp_scene.name}")
        
        # Store the original scene to restore later
        original_scene = bpy.context.window.scene
        
        # Make the new scene active for operations
        bpy.context.window.scene = temp_scene
        print(f"oneShot: Set active scene to: {temp_scene.name}")

        # Ensure sequence editor exists
        if not temp_scene.sequence_editor:
            temp_scene.sequence_editor_create()
            print("oneShot: Sequence editor created for temporary scene.")
        else:
            print("oneShot: Sequence editor already exists for temporary scene.")

        # Add the video as a movie strip
        bpy.ops.sequencer.movie_strip_add(filepath=video_path, frame_start=1)
        print(f"oneShot: Added movie strip from {video_path}.")

        # Get a reference to the newly created video strip
        movie_strip = None
        for strip in temp_scene.sequence_editor.sequences:
            if strip.type == 'MOVIE' and strip.filepath == video_path:
                movie_strip = strip
                break
        
        if not movie_strip:
            print(f"Error: Could not find movie strip for {video_path}")
            return False
        print(f"oneShot: Found movie strip: {movie_strip.name}")

        # Set the temporary scene's frame_end to match the video strip's duration
        temp_scene.frame_end = movie_strip.frame_final_duration
        print(f"oneShot: Set scene frame_end to: {temp_scene.frame_end}")

        # Configure the scene's render settings
        temp_scene.render.filepath = output_dir
        temp_scene.render.image_settings.file_format = 'PNG'
        temp_scene.render.image_settings.color_mode = 'RGB'
        print(f"oneShot: Configured render settings: filepath={output_dir}, format=PNG, color_mode=RGB")

        # Run the animation render
        print("oneShot: Starting animation render...")
        bpy.ops.render.render(animation=True, scene=temp_scene.name)
        print("oneShot: Animation render complete.")

        print("oneShot: Frame extraction successful.")
        return True

    except Exception as e:
        print(f"oneShot Error: An error occurred during frame extraction: {e}")
        return False
    finally:
        print("oneShot: Entering finally block for cleanup.")
        # Restore original scene context
        if temp_scene and original_scene:
            bpy.context.window.scene = original_scene
            print(f"oneShot: Restored original scene: {original_scene.name}")
        
        # Ensure the temporary scene is deleted
        if temp_scene and temp_scene.name in bpy.data.scenes:
            print(f"oneShot: Deleting temporary scene: {temp_scene.name}")
            bpy.data.scenes.remove(temp_scene)
            print("oneShot: Temporary scene deleted.")
