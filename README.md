# oneShot

oneShot is a Blender addon that allows you to create a 3D scene from a video file using photogrammetry. It uses COLMAP as the underlying reconstruction software.

## Features

*   **Video to 3D Scene:** Generate a 3D scene directly from a video file.
*   **Automatic COLMAP Installation:** oneShot can download and install the correct version of COLMAP for your operating system (Windows or Linux).
*   **Customizable Settings:** Control the quality of the reconstruction and other parameters.
*   **Non-blocking UI:** The photogrammetry process runs in a background thread, so Blender's UI remains responsive.
*   **Progress Indicator:** A progress bar in the UI shows the status of the reconstruction process.

## Installation

1.  Download the latest release of the addon from the [releases page](https://github.com/notacarrrot/oneShot/releases).
2.  Open Blender and go to `Edit > Preferences > Add-ons`.
3.  Click `Install` and select the downloaded `.zip` file.
4.  Enable the addon by checking the box next to its name.

## How to Use

1.  **Install COLMAP:**
    *   Open the addon's preferences (`Edit > Preferences > Add-ons > oneShot`).
    *   Click the "Download & Install COLMAP" button. The addon will download and install COLMAP in the background.
    *   The path to the COLMAP executable will be automatically filled in.

2.  **Generate a 3D Scene:**
    *   In the 3D View, open the sidebar (press `N`).
    *   Go to the "oneShot" panel.
    *   Click the folder icon to select a video file.
    *   Click the "Generate 3D Scene" button.
    *   The reconstruction process will start, and you can monitor the progress in the panel.

## Settings

### Main Settings

*   **Video Path:** The path to the input video file.

### Advanced Settings

*   **Image Format:** The format of the frames extracted from the video (PNG or JPG).
*   **COLMAP Quality:** The quality of the COLMAP reconstruction (Low, Medium, High, Extreme). Higher quality settings will take longer to process.
*   **Delete Workspace on Finish:** If checked, the temporary workspace created by COLMAP will be deleted after the reconstruction is finished.

## Contributing

Contributions are welcome! If you find a bug or have a feature request, please open an issue on the [GitHub repository](https://github.com/notacarrrot/oneShot/issues).

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.