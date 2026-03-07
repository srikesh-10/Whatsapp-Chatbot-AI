import ffmpeg
import os
from pathlib import Path

def _add_winget_ffmpeg_to_path() -> None:
    """Add FFmpeg to PATH when installed with winget in the current user profile."""
    local_app_data = os.getenv("LOCALAPPDATA")
    if not local_app_data:
        return

    packages_root = Path(local_app_data) / "Microsoft" / "WinGet" / "Packages"
    if not packages_root.exists():
        return

    candidate_dirs = list(packages_root.glob("Gyan.FFmpeg*"))
    for candidate in candidate_dirs:
        bin_dir = candidate / "ffmpeg-8.0.1-full_build" / "bin"
        if (bin_dir / "ffmpeg.exe").exists():
            if str(bin_dir) not in os.environ.get("PATH", ""):
                os.environ["PATH"] = os.environ.get("PATH", "") + os.pathsep + str(bin_dir)
            return


_add_winget_ffmpeg_to_path()

def convert_to_wav(input_path: str, output_path: str) -> str:
    """
    Converts any audio file to WAV format using ffmpeg.
    Returns the path to the newly created WAV file.
    """
    try:
        (
            ffmpeg
            .input(input_path)
            .output(output_path, format='wav', acodec='pcm_s16le', ac=1, ar='16k')
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        return output_path
    except ffmpeg.Error as e:
        print(f"FFmpeg error: {e.stderr.decode('utf-8')}")
        raise e
