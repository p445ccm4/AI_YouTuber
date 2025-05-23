import argparse
import logging
from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip, afx
import numpy as np
import soundfile as sf
from diffusers import StableAudioPipeline

class MusicGenerator:
    def __init__(self, logger:logging.Logger=None):
        self.logger = logger
        self.model = None

    def _load_model(self):
        if not self.model:
            self.logger.info("Loading Stable Audio model...")
            self.pipe = StableAudioPipeline.from_pretrained(
                "./models/stable-audio-open-1.0", 
                ).to("cpu")
            self.logger.info("Stable Audio model loaded.")

    def generate_music(self, prompt, input_video_path, output_audio_path):
        n_waveforms = int(VideoFileClip(input_video_path).duration / 47) + 1
        self._load_model()

        # run the generation
        self.pipe = self.pipe.to("cuda")

        all_outputs = []
        batch_size = 4
        
        for i in range(0, n_waveforms, batch_size):
            # Calculate how many waveforms to generate in this batch
            current_batch_size = min(batch_size, n_waveforms - i)
            
            audios = self.pipe(
            prompt,
            negative_prompt="low quality, human vocal voice",
            num_inference_steps=100,
            num_waveforms_per_prompt=current_batch_size,
            ).audios
            
            output = audios.float().cpu().numpy()
            output = output.transpose(0, 2, 1)
            all_outputs.append(output)
            
            self.logger.info(f"Generated batch {i//batch_size + 1} of {(n_waveforms + batch_size - 1)//batch_size}")
            
        self.pipe = self.pipe.to("cpu")

        output = np.concatenate([np.concatenate(batch, axis=0) for batch in all_outputs], axis=0)
        
        sf.write(output_audio_path, output, self.pipe.vae.sampling_rate)
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
            audio_clip = audio_clip.subclipped(start, end).with_start(0.0)

        # Combine video and audio
        final_audio = CompositeAudioClip([video_clip.audio, audio_clip])
        video_clip.audio = final_audio

        # Write the result to a file
        video_clip.write_videofile(output_video_path, ffmpeg_params=["-hide_banner", "-loglevel", "error"])

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

    if not args.music_path and not args.prompt:
        raise ValueError("Either music_path or prompt must be provided.")
    if not args.music_path:
        args.music_path = "music.wav"  # default name

    # music_adder.generate_music(args.prompt, args.input_video_path, args.music_path)
    music_adder.add_background_music(args.input_video_path, args.music_path, args.output_video_path)