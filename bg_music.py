import argparse
import os
import argparse
import os
import logging
from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip

class BackgroundMusicAdder:
    def __init__(self, logger=None):
        self.logger = logger if logger else logging.getLogger(__name__)

    def add_background_music(self, input_video_path, music_path, output_video_path):
        """
        Adds background music to a video using MoviePy.
        """
        try:
            video_clip = VideoFileClip(input_video_path).with_volume_scaled(1.5)
            audio_clip = AudioFileClip(music_path).with_volume_scaled(0.3)

            # Ensure the music is as long as the video
            start = audio_clip.duration/2 - video_clip.duration/2
            end = audio_clip.duration/2 + video_clip.duration/2
            audio_clip = audio_clip.subclipped(start, end)

            # Combine video and audio
            final_audio = CompositeAudioClip([video_clip.audio, audio_clip])
            video_clip.audio = final_audio

            # Write the result to a file
            video_clip.write_videofile(output_video_path, logger=None)

            # Delete the original video
            os.remove(input_video_path)

            self.logger.info(f"Successfully added background music to {input_video_path} and saved as {output_video_path}")

        except Exception as e:
            self.logger.error(f"An error occurred: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    parser = argparse.ArgumentParser(description="Add background music to a video.")
    parser.add_argument("--input_video_path", help="Path to the video file")
    parser.add_argument("--music_path", help="Path to the audio file (background music)")
    parser.add_argument("--output_video_path", help="Path to save the video with background music")

    args = parser.parse_args()

    music_adder = BackgroundMusicAdder(logger=logging.getLogger(__name__))
    music_adder.add_background_music(args.input_video_path, args.music_path, args.output_video_path)
