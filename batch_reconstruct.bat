:: ================================================================
::  BATCH SCRIPT FOR AUTOMATED PHOTOGRAMMETRY TRACKING WORKFLOW
::  By polyfjord - https://youtube.com/polyfjord
:: ================================================================
::  USAGE
::    • Double-click this .bat or run it from a command prompt.  
::    • Frames are extracted, features matched, and a sparse
::      reconstruction is produced automatically.  
::    • Videos that have already been processed are skipped on
::      subsequent runs.
::
::  PURPOSE
::    This is a fully automated photogrammetry tracker for turning
::    videos into COLMAP sparse models with robust error handling,
::    clean directory setup, and clear ✖ / ✔ logging.
::
::  FOLDER LAYOUT (all folders sit side-by-side):
::    01 COLMAP   – Download the latest release from
::                   https://github.com/colmap/colmap
::                   and place colmap.bat (plus its dlls) here.
::
::    02 VIDEOS   – Put your input video files (.mp4, .mov, …) here.
::                   All framerates and aspect ratios are supported.
::
::    03 FFMPEG   – Drop a **static build** of FFmpeg
::                   (either ffmpeg.exe or bin\ffmpeg.exe) here.
::
::    04 SCENES   – The script creates one sub-folder per video
::                   containing extracted frames, the COLMAP
::                   database, sparse model, and TXT export.
::
::    05 SCRIPTS  – This batch file lives here.
::
:: ================================================================
@echo off

:: ---------- Resolve top-level folder (one up from this .bat) -----
pushd "%~dp0\.." >nul
set "TOP=%cd%"
popd >nul

:: ---------- Key paths -------------------------------------------
set "COLMAP_DIR=%TOP%\01 COLMAP"
set "VIDEOS_DIR=%TOP%\02 VIDEOS"
set "FFMPEG_DIR=%TOP%\03 FFMPEG"
set "SCENES_DIR=%TOP%\04 SCENES"

:: ---------- Locate ffmpeg.exe -----------------------------------
if exist "%FFMPEG_DIR%\ffmpeg.exe" (
    set "FFMPEG=%FFMPEG_DIR%\ffmpeg.exe"
) else if exist "%FFMPEG_DIR%\bin\ffmpeg.exe" (
    set "FFMPEG=%FFMPEG_DIR%\bin\ffmpeg.exe"
) else (
    echo [ERROR] ffmpeg.exe not found inside "%FFMPEG_DIR%".
    pause & goto :eof
)

:: ---------- Locate colmap.exe (skip the .bat) --------------------
if exist "%COLMAP_DIR%\colmap.exe" (
    set "COLMAP=%COLMAP_DIR%\colmap.exe"
) else if exist "%COLMAP_DIR%\bin\colmap.exe" (
    set "COLMAP=%COLMAP_DIR%\bin\colmap.exe"
) else (
    echo [ERROR] colmap.exe not found inside "%COLMAP_DIR%".
    pause & goto :eof
)

:: ---------- Put COLMAP’s dll folder(s) on PATH -------------------
set "PATH=%COLMAP_DIR%;%COLMAP_DIR%\bin;%PATH%"

:: ---------- Ensure required folders exist ------------------------
if not exist "%VIDEOS_DIR%" (
    echo [ERROR] Input folder "%VIDEOS_DIR%" missing.
    pause & goto :eof
)
if not exist "%SCENES_DIR%" mkdir "%SCENES_DIR%"

:: ---------- Count videos for progress bar ------------------------
for /f %%C in ('dir /b /a-d "%VIDEOS_DIR%\*" ^| find /c /v ""') do set "TOTAL=%%C"
if "%TOTAL%"=="0" (
    echo [INFO] No video files found in "%VIDEOS_DIR%".
    pause & goto :eof
)

echo ==============================================================
echo  Starting COLMAP on %TOTAL% video(s) …
echo ==============================================================

setlocal EnableDelayedExpansion
set /a IDX=0

for %%V in ("%VIDEOS_DIR%\*.*") do (
    if exist "%%~fV" (
        set /a IDX+=1
        call :PROCESS_VIDEO "%%~fV" "!IDX!" "%TOTAL%"
    )
)

echo --------------------------------------------------------------
echo  All jobs finished – results are in "%SCENES_DIR%".
echo --------------------------------------------------------------
pause
goto :eof


:PROCESS_VIDEO
:: ----------------------------------------------------------------
::  %1 = full path to video   %2 = current index   %3 = total
:: ----------------------------------------------------------------
setlocal
set "VIDEO=%~1"
set "NUM=%~2"
set "TOT=%~3"

for %%I in ("%VIDEO%") do (
    set "BASE=%%~nI"
    set "EXT=%%~xI"
)

echo.
echo [!NUM!/!TOT!] === Processing "!BASE!!EXT!" ===

:: -------- Directory layout for this scene -----------------------
set "SCENE=%SCENES_DIR%\!BASE!"
set "IMG_DIR=!SCENE!\images"
set "SPARSE_DIR=!SCENE!\sparse"

:: -------- Skip if already reconstructed -------------------------
if exist "!SCENE!" (
    echo        ↻ Skipping "!BASE!" – already reconstructed.
    goto :END
)

:: Clean slate ----------------------------------------------------
mkdir "!IMG_DIR!"   >nul
mkdir "!SPARSE_DIR!" >nul

:: -------- 1) Extract every frame --------------------------------
echo        [1/4] Extracting frames …
"%FFMPEG%" -loglevel error -stats -i "!VIDEO!" -qscale:v 2 ^
    "!IMG_DIR!\frame_%%06d.jpg"
if errorlevel 1 (
    echo        ✖ FFmpeg failed – skipping "!BASE!".
    goto :END
)

:: Check at least one frame exists
dir /b "!IMG_DIR!\*.jpg" >nul 2>&1 || (
    echo        ✖ No frames extracted – skipping "!BASE!".
    goto :END
)

:: -------- 2) Feature extraction ---------------------------------
echo        [2/4] COLMAP feature_extractor …
"%COLMAP%" feature_extractor ^
    --database_path "!SCENE!\database.db" ^
    --image_path    "!IMG_DIR!" ^
    --ImageReader.single_camera 1 ^
    --SiftExtraction.use_gpu 1 ^
    --SiftExtraction.max_image_size 4096
if errorlevel 1 (
    echo        ✖ feature_extractor failed – skipping "!BASE!".
    goto :END
)

:: -------- 3) Sequential matching --------------------------------
echo        [3/4] COLMAP sequential_matcher …
"%COLMAP%" sequential_matcher ^
    --database_path "!SCENE!\database.db" ^
    --SequentialMatching.overlap 15
if errorlevel 1 (
    echo        ✖ sequential_matcher failed – skipping "!BASE!".
    goto :END
)

:: -------- 4) Sparse reconstruction ------------------------------
echo        [4/4] COLMAP mapper …
"%COLMAP%" mapper ^
    --database_path "!SCENE!\database.db" ^
    --image_path    "!IMG_DIR!" ^
    --output_path   "!SPARSE_DIR!" ^
    --Mapper.num_threads %NUMBER_OF_PROCESSORS%
if errorlevel 1 (
    echo        ✖ mapper failed – skipping "!BASE!".
    goto :END
)

:: -------- Export best model to TXT ------------------------------
if exist "!SPARSE_DIR!\0" (
    "%COLMAP%" model_converter ^
        --input_path  "!SPARSE_DIR!\0" ^
        --output_path "!SPARSE_DIR!" ^
        --output_type TXT >nul
)

echo        ✔ Finished "!BASE!"  (!NUM!/!TOT!)

:END
endlocal & goto :eof
