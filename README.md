```
 ________  ________   _______   ________  ___  ___  ________  _________   
|\   __  \|\   ___  \|\  ___ \ |\   ____\|\  \|\  \|\   __  \|\___   ___\ 
\ \  \|\  \ \  \\ \  \ \   __/|\ \  \___|\ \  \\\  \ \  \|\  \|___ \  \_| 
 \ \  \\\  \ \  \\ \  \ \  \_|/_\ \_____  \ \   __  \ \  \\\  \   \ \  \  
  \ \  \\\  \ \  \\ \  \ \  \_|\ \|____|\  \ \  \ \  \ \  \\\  \   \ \  \ 
   \ \_______\ \__\\ \__\ \_______\____\_\  \ \__\ \__\ \_______\   \ \__\
    \|_______|\|__| \|__|\|_______|\_________\|__|\|__|\|_______|    \|__|
                                  \|_________|                            
                                                      
```                                                                       
# One-Click Photogrammetry & Camera Tracking for Blender

**oneShot** is a powerful Blender addon that automates the entire process of creating 3D scenes from video footage or image sequences. It provides a complete, self-contained photogrammetry pipeline by integrating the power of **FFmpeg** and **COLMAP** into a user-friendly, single-click interface.

![oneShot Demo](https://github.com/notacarrrot/oneShot/blob/main/video-OUT/addon-demo.gif)

Whether you're a VFX artist creating camera tracks, a 3D archivist preserving artifacts, or an indie developer building game assets, oneShot handles the complex technical pipeline, letting you focus on the creative result.

[![Blender Version](https://img.shields.io/badge/Blender-4.0%2B-orange.svg)](https://www.blender.org/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Release](https://img.shields.io/github/v/release/notacarrrot/oneShot)]()


<h2 id="Table">📋 Table of Contents</h2>

  - [✨ Features](#Features)
  - [🚀 Installation](#Installation)
  - [🛠️ Usage & Workflow](#Usage)
      - [One-Time Setup: Installing Dependencies](#Dependencies)
      - [The Main Workflow: From Video to 3D Scene](#Workflow)
      - [Post-Processing: Optimising the Scene](#Optimising)
  - [🎛️ UI and Button Reference](#Button)
  - [⚙️ Advanced Settings](#Advanced)
  - [🚑 Troubleshooting](#Troubleshooting)
  - [❤️ Credits & License](#Credits)


<h2 id="Features">✨ Features</h2>

  * **One-Click Dependencies:** Automatically downloads and installs the correct versions of COLMAP and FFmpeg for your OS. No manual setup required\!
  * **Unified Workflow:** A single **"Generate Scene"** button intelligently detects your input—whether it's a video file or a folder of images—and runs the entire pipeline from start to finish.
  * **Responsive UI:** The reconstruction process runs in a background thread, so Blender remains fully responsive while you monitor live progress in the addon panel.
  * **Scene Optimization:** A dedicated **"Optimise Scene"** button prepares your generated scene for animation by creating a 50% video proxy, re-orienting the entire reconstruction for a better starting angle, and cleaning up the outliner.
  * **Advanced Control:** A comprehensive "Advanced Settings" panel gives power users fine-grained control over camera and point cloud import settings.
  * **Direct COLMAP Import:** Already have a COLMAP model? A separate panel allows you to import it directly, bypassing the generation step.


<h2 id="Installation">🚀 Installation</h2>

1.  Go to the [Releases](https://github.com/notacarrrot/oneShot/releases) page.
2.  Download the latest `oneShot.zip` file.
3.  In Blender, go to `Edit > Preferences > Add-ons`.
4.  Click `Install > From Local` and select the downloaded `oneShot.zip` file.
5.  Enable the "oneShot" addon by checking the box next to it.


<h2 id="Usage">🛠️ Usage & Workflow</h2>

The entire process is managed from the **oneShot panel** in the 3D View's sidebar (press `N` to open).

<h3 id="Dependencies">One-Time Setup: Installing Dependencies</h3>

Before you begin, you must install the addon's dependencies. This is a one-time action.

![oneShot install Demo](https://github.com/notacarrrot/oneShot/blob/main/video-OUT/installation-demo.gif)

1.  Go to `Edit > Preferences > Add-ons` and find the "oneShot" addon.
2.  Expand the addon's preferences panel.
3.  Click the **"Download & Install COLMAP"** button. Wait for the process to complete (check the system console for progress).
4.  Click the **"Download & Install FFmpeg"** button.
5.  Click the **"Importer Dependencies"** button.
6.  Once all are installed, the paths to the executables will be filled in automatically. You are now ready to use the addon.

<h3 id="Workflow">The Main Workflow: From Video to 3D Scene</h3>

The two-step process has been replaced by a single, intelligent pipeline.

1.  **Select Input Path:** Click the folder icon and select either a **video file** (`.mp4`, `.mov`, etc.) OR a **folder containing an image sequence**. The addon will automatically detect the input type.
2.  **Select Output Scene Folder:** Choose a root directory where your project files will be saved. oneShot will automatically create a new subfolder inside this directory named after your video file.
3.  **Adjust Quality (Optional):** Set the **Max Image Resolution** for COLMAP to process. A lower value (e.g., 1920) is much faster than the original resolution and often yields similar quality results. Set to 0 to use the original size.
4.  **Click Generate Scene:** The addon will now perform all necessary steps in the background:
      * If a video is provided, it extracts the frames.
      * It runs the full COLMAP reconstruction pipeline.
      * It imports the final camera track and point cloud into Blender.
      * It sets the scene's output resolution to match the original video.
5.  You can monitor the progress live in the panel and cancel the operation at any time by clicking the **Stop** button.

<h3 id="Optimising">Post-Processing: Optimising the Scene</h3>

After the generation is complete, a single click can prepare the scene for animation.

1.  Click the **"Optimise Scene"** button.
2.  The operator will perform several actions:
      * **Generate Proxy:** It creates a 50% resolution proxy of the original video for smooth viewport playback.
      * **Update Camera:** It links the animated camera's background to this new proxy file.
      * **Re-orient Scene:** It precisely rotates the entire reconstruction so that the first camera (`frame_000000_cam`) is upright and level, giving you a convenient starting point.
      * **Clean Up:** It hides the collection of individual cameras and organizes the final objects for a clean outliner.


<h2 id="Button">🎛️ UI and Button Reference</h2>

| Panel | Button / Setting | Description |
| :--- | :--- | :--- |
| **Add-on Preferences** | `Download & Install COLMAP` | Downloads and configures the COLMAP executable in a `deps` folder inside the addon. |
| | `Download & Install FFmpeg` | Downloads and configures the FFmpeg executable. |
| **oneShot Workflow** | `Input Path` | File browser to select your source video file or image sequence folder. |
| | `Output Scene Folder` | File browser to select the root directory for your project files. |

| | `Generate Scene` | Starts the entire automated pipeline: frame extraction (if needed), COLMAP processing, and import into Blender. |
| | `Stop` | Immediately terminates the ongoing FFmpeg or COLMAP process. |
| | `Optimise Scene` | A post-processing tool that generates a video proxy, re-orients the scene, and cleans up the outliner for animation. |
| **Direct Import** | `COLMAP Model Path` | For users who already have a processed COLMAP model folder. |
| | `Import Model` | Imports the specified COLMAP model using the settings in the "Advanced Settings" panel. |


<h2 id="Advanced">⚙️ Advanced Settings</h2>

For power users, the "Advanced Settings" panel (collapsed by default) provides fine-grained control over how the final data is imported into Blender. These settings are inherited from the powerful Photogrammetry Importer addon and are applied during the final import stage of the "Generate Scene" process or when using "Direct Import".

  * **Import Cameras:** Control camera visibility, background images, image planes, and depth maps.
  * **Add Camera Motion as Animation:** Control settings for the final animated camera, including interpolation, frame adjustments, and background video.
  * **Import Points:** Control how the point cloud is generated, including sparsity, whether it's drawn via GPU or as a mesh object, and initial point size.


<h2 id="Troubleshooting">🚑 Troubleshooting</h2>

  * **Installation buttons don't work:** Your computer's firewall or antivirus might be blocking the download. Check your security settings and ensure Blender has internet access.
  * **"Generate 3D Scene" fails:** Check the system console (`Window > Toggle System Console`) for detailed error messages from COLMAP. Common issues include:
      * Blurry or low-quality video footage.
      * Not enough parallax (side-to-side movement) in the video.
      * Reflective surfaces or moving objects in the scene.
  * **"Optimise Scene" button is greyed out or fails:** This button relies on objects with specific names created by the generation process (e.g., "Animated Camera", "Reconstruction Collection"). If you have renamed these objects or the generation failed, the button will not work.


<h2 id="Credits">❤️ Credits & License</h2>

This addon stands on the shoulders of giants.

  * **COLMAP:** The core reconstruction engine. [Project Website](https://colmap.github.io/)
  * **FFmpeg:** The tool used for robust video frame extraction. [Project Website](https://ffmpeg.org/)
  * **Photogrammetry Importer:** The original addon by SBCV, whose powerful import logic is bundled into oneShot. [GitHub Repository](https://github.com/SBCV/Blender-Addon-Photogrammetry-Importer)

This project is licensed under the MIT License. See the `LICENSE` file for details.
