import subprocess
from gtts import gTTS
import argparse
import os
import logging

class AudioGenerator:
    def __init__(self, logger=None):
        self.logger = logger if logger else logging.getLogger(__name__)

    def generate_audio(self, caption, output_audio_path, speed_factor=1.5):
        temp_audio_path = output_audio_path.replace(".mp3", "_temp.mp3")
        audio = gTTS(caption, lang="en", tld="us") # lang="yue" for Cantonese, (lang="en", tld="us") for US English
        audio.save(temp_audio_path)
        audio_path = temp_audio_path.replace("_temp", "")
        if os.path.exists(audio_path):
            os.remove(audio_path)
        subprocess.call([
            "ffmpeg",
            "-hide_banner",
            "-loglevel", "error",
            "-i", temp_audio_path,
            "-filter:a", f"atempo={speed_factor}",
            audio_path
        ])
        os.remove(temp_audio_path)
        self.logger.info(f"Generated audio: {audio_path}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(description="Generate videos from text prompts.")
    parser.add_argument("-c", "--caption", type=str, required=True, help="Caption")
    parser.add_argument("-o", "--output_audio_path", type=str, required=True, help="Output audio path")
    args = parser.parse_args()

    generator = AudioGenerator(logger)
    generator.generate_audio(args.c, args.o)
