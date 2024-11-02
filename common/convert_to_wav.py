import os
import subprocess

path = "audio.wav"
new_base_name = "audio_converted"

# Determine the parent folder of the given path
parent_folder = os.path.dirname(path)

# Construct the path for the converted audio file
converted_audio = os.path.join(parent_folder, f"{new_base_name}.wav")

# Check if the converted audio file already exists
if not os.path.exists(converted_audio):
    # Use ffmpeg to convert the audio file
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "warning",
            "-i",
            path,
            "-vn",
            "-acodec",
            "pcm_s16le",
            "-ar",
            "44100",
            "-ac",
            "2",
            converted_audio,
        ]
    )
