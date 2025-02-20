import argparse
import os
import argparse
import os
import logging
from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip, afx
from InspireMusic.inspiremusic.cli.inference import set_env_variables, InspireMusicUnified

class MusicGenerator:
    def __init__(self, logger=None):
        self.logger = logger

    def generate_music(self, prompt, output_audio_path):
        set_env_variables()
        model = InspireMusicUnified(model_name = "InspireMusic-1.5B-Long", model_dir="./models/InspireMusic-1.5B-Long", result_dir=os.path.dirname(output_audio_path))
        model.inference("text-to-music", prompt, output_fn=os.path.basename(output_audio_path).split('.')[0])
        self.logger.info(f"Generated music saved to {output_audio_path}")

    def add_background_music(self, input_video_path, music_path, output_video_path):
        """
        Adds background music to a video using MoviePy.
        """
        video_clip = VideoFileClip(input_video_path).with_volume_scaled(2)
        audio_clip = AudioFileClip(music_path).with_effects([afx.AudioNormalize()]).with_volume_scaled(0.3)

        # Play the middle part of the music if it is longer than the video
        if audio_clip.duration > video_clip.duration:
            start = audio_clip.duration/2 - video_clip.duration/2
            end = audio_clip.duration/2 + video_clip.duration/2
            audio_clip = audio_clip.subclipped(start, end)

        # Combine video and audio
        final_audio = CompositeAudioClip([video_clip.audio, audio_clip])
        video_clip.audio = final_audio

        # Write the result to a file
        video_clip.write_videofile(output_video_path, logger=None)

        # # Delete the original video
        # os.remove(input_video_path)

        self.logger.info(f"Successfully added background music to {input_video_path} and saved as {output_video_path}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    parser = argparse.ArgumentParser(description="Add background music to a video.")
    parser.add_argument("--input_video_path", help="Path to the video file", required=True)
    parser.add_argument("--music_path", help="Path to the audio file (background music)", required=False)
    parser.add_argument("--output_video_path", help="Path to save the video with background music", required=True)
    parser.add_argument("--prompt", help="Prompt to generate music", required=False)

    args = parser.parse_args()

    music_adder = MusicGenerator(logger=logging.getLogger(__name__))

    if not args.music_path and args.prompt:
        args.music_path = "generated_music.wav"  # default name
        music_adder.generate_music(args.prompt, args.music_path)
    elif not args.music_path and not args.prompt:
        raise ValueError("Either music_path or prompt must be provided.")

    music_adder.add_background_music(args.input_video_path, args.music_path, args.output_video_path)
