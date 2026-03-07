import ffmpeg
import os

# Add FFmpeg path to environment for Windows if installed via WinGet
WINGET_FFMPEG_PATH = r"C:\Users\srike\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0.1-full_build\bin"
if os.path.exists(WINGET_FFMPEG_PATH):
    os.environ["PATH"] += os.pathsep + WINGET_FFMPEG_PATH

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
