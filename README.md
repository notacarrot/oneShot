```
 ______     __   __     ______     ______     __  __     ______     ______  
/\  __ \   /\ "-.\ \   /\  ___\   /\  ___\   /\ \_\ \   /\  __ \   /\__  _\ 
\ \ \/\ \  \ \ \-.  \  \ \  __\   \ \___  \  \ \  __ \  \ \ \/\ \  \/_/\ \/ 
 \ \_____\  \ \_\\"\_\  \ \_____\  \/\_____\  \ \_\ \_\  \ \_____\    \ \_\ 
  \/_____/   \/_/ \/_/   \/_____/   \/_____/   \/_/\/_/   \/_____/     \/_/ 
                                                                            ____/                                                       
```                                                                                                                                                                                                                                                                                                                                                      
# One-Click Photogrammetry and Camera Tracking for Blender


**oneShot** is a powerful Blender addon that dramatically simplifies the process of creating 3D scenes from video footage. It provides a complete, self-contained photogrammetry pipeline by integrating the power of **FFmpeg** and **COLMAP** directly into a user-friendly, two-step interface.

Whether you're a VFX artist, a 3D archivist, or just exploring photogrammetry, oneShot automates the tedious parts, letting you focus on the creative result.

[![Blender Version](https://img.shields.io/badge/Blender-4.0%2B-orange.svg)](https://www.blender.org/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)]()


## ✨ Features

* **One-Click Dependencies:** Automatically downloads and installs the correct versions of COLMAP and FFmpeg for your OS. No manual setup required!
* **Simple Two-Step Workflow:** A clean, intuitive UI guides you through the process: first extract frames, then reconstruct the scene.
* **Bring Your Own Frames:** Already have an image sequence? Skip the video extraction and jump straight to the reconstruction step.
* **Advanced Customization:** An optional dropdown provides control over reconstruction quality, image formats, and more for advanced users.
* **Responsive UI:** The reconstruction process runs in a background thread, so Blender remains fully responsive while you monitor the live progress.
* **Self-Contained:** All necessary components are bundled within the addon, providing a seamless experience without needing to install multiple separate addons.


## 🎬 Demo

Here's a quick look at the oneShot workflow in action.

**(GIF Placeholder: Show the addon preferences, clicking the 'Download & Install' buttons for COLMAP and FFmpeg.)**
*Fig 1: Automated installation of dependencies from the addon preferences.*

**(GIF Placeholder: Show the 'Step 1' panel, selecting a video, an output folder, and clicking 'Extract Frames'.)**
*Fig 2: Extracting an image sequence from a video file.*

**(GIF Placeholder: Show the 'Step 2' panel, selecting the image folder, clicking 'Generate 3D Scene', and the final imported camera/point cloud.)**
*Fig 3: Reconstructing the 3D scene from the image sequence and importing it into Blender.*


## 🚀 Installation

1.  Go to the [Releases](https://www.google.com/search?q=https://github.com/your-username/oneShot/releases) page.
2.  Download the latest `oneShot.zip` file.
3.  In Blender, go to `Edit > Preferences > Add-ons`.
4.  Click `Install...` and select the downloaded `oneShot.zip` file.
5.  Enable the "oneShot" addon by checking the box next to it.


## 🛠️ Usage & Workflow

The entire process is managed from the **oneShot panel** in the 3D View's sidebar (press `N` to open).

### Initial Setup: Installing Dependencies

Before you begin, you must install the addon's dependencies. This is a one-time setup.

1.  Go to `Edit > Preferences > Add-ons` and find the "oneShot" addon.
2.  Expand the addon's preferences panel.
3.  Click the **"Download & Install COLMAP"** button. Wait for the process to complete (check the system console for progress).
4.  Click the **"Download & Install FFmpeg"** button.
5.  Once both are installed, the paths to the executables will be filled in automatically. You are now ready to use the addon.

### Step 1: Extract Frames from Video

This step converts your video file into a sequence of images that COLMAP can process.

1.  In the oneShot panel, under **"Step 1: Extract Frames"**, click the folder icon next to **"Video Input"** and select your video file (`.mp4`, `.mov`, etc.).
2.  Click the folder icon next to **"Image Output Folder"** and choose an **empty folder** where the frames will be saved.
3.  Click the **"Extract Frames to Folder"** button. The process will run, and you can monitor its progress in Blender's system console.

### Step 2: Reconstruct 3D Scene

This step takes a folder of images, processes them with COLMAP, and imports the resulting 3D camera and point cloud into your scene.

1.  In the oneShot panel, under **"Step 2: Reconstruct Scene"**, click the folder icon next to **"Image Input Folder"**.
2.  Select the folder containing the image sequence you just created (or your own pre-existing sequence).
3.  Click the **"Generate 3D Scene"** button.
4.  The process will begin, and you can monitor its status live in the UI via the progress bar. This step can take a long time depending on the number of images and the selected quality. Blender will remain responsive.
5.  Once complete, a new collection containing the animated camera and the point cloud will be added to your scene.


## ⚙️ Advanced Settings

For more control over the reconstruction, you can expand the "Advanced Settings" dropdown in the Step 2 panel:

* **Image Format:** Choose between PNG and JPG for frame extraction. JPG is faster and uses less space, but PNG is lossless.
* **COLMAP Quality:** Adjust the detail level for feature matching. Higher settings are more accurate but significantly slower.
* **Delete Workspace:** If checked, the temporary COLMAP processing files will be deleted after the import is complete, saving disk space.


## 🚑 Troubleshooting

* **Installation buttons don't work:** Your computer's firewall or antivirus might be blocking the download. Check your security settings and ensure Blender has internet access.
* **"Generate 3D Scene" fails:** Check the system console (`Window > Toggle System Console`) for detailed error messages from COLMAP. Common issues include:
    * Blurry or low-quality video footage.
    * Not enough parallax or movement in the video.
    * Reflective surfaces or moving objects in the scene.
* **Addon doesn't enable:** Ensure you are using Blender 4.0 or newer.



## ❤️ Credits & License

This addon stands on the shoulders of giants.

* **COLMAP:** The core reconstruction engine. [Project Website](https://colmap.github.io/)
* **FFmpeg:** The tool used for robust video frame extraction. [Project Website](https://ffmpeg.org/)
* **Photogrammetry Importer:** The original addon by SBCV, whose powerful import logic is bundled into oneShot. [GitHub Repository](https://github.com/SBCV/Blender-Addon-Photogrammetry-Importer)

This project is licensed under the MIT License. See the [LICENSE](https://www.google.com/search?q=LICENSE) file for details.
