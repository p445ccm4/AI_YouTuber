import os
import json
import argparse
import logging
import traceback
import gen_audio, gen_video, gen_freeze_video, interpolate, audio_caption, concat, gen_music

class YTShortsMaker:
    def __init__(self, json_file, working_dir, existed_music_path, indices_to_process=None, logger=None):
        self.json_file = json_file
        self.working_dir = working_dir
        self.existed_music_path = existed_music_path
        self.indices_to_process = indices_to_process
        self.failed_indices = []
        self.logger = logger if logger else logging.getLogger(__name__)
        self.audio_generator = gen_audio.AudioGenerator(logger=self.logger, reference_audio=f"{self.working_dir}/0.wav")
        self.video_generator = gen_video.VideoGenerator(logger=self.logger)
        self.freeze_video_generator = gen_freeze_video.FreezeVideoGenerator(logger=self.logger)
        self.interpolator = interpolate.FrameInterpolator(logger=self.logger)
        self.captioner = audio_caption.VideoCaptioner(logger=self.logger)
        self.concatenator = concat.VideoConcatenator(self.working_dir, logger=self.logger)
        self.bg_music_adder = gen_music.MusicGenerator(logger=self.logger)

    def run(self):
        os.makedirs(self.working_dir, exist_ok=True)
        failed_indices = []

        with open(self.json_file, 'r') as f:
            data = json.load(f)
            script = data.get('script', data.get('proposal'))
            thumbnail = data.get('thumbnail')
            music = data.get('music', None)
        
        if self.indices_to_process is not None and -1 not in self.indices_to_process:
            self.logger.debug(f"Skipping thumbnail generation as -1 is not in the provided indices.")
        else:
            try:
                title = thumbnail.get('title')
                prompt = thumbnail.get('prompt')

                # 1. Generate thumbnail
                self.freeze_video_generator.generate_freeze_video(
                    prompt=prompt,
                    index=-1,
                    output_video_path=f"{self.working_dir}/-1.mp4",
                    num_frames=5
                )

                # 2. Add caption to thumbnail
                self.captioner.add_audio_and_caption(
                    audio_path=None,
                    caption=title,
                    input_video_path=f"{self.working_dir}/-1.mp4",
                    output_video_path=f"{self.working_dir}/-1_captioned.mp4",
                    title=True
                )
            except Exception:
                self.logger.error(f"Error processing thumbnail: \n{print(traceback.format_exc())}")
                self.failed_indices.append("thumbnail")
        
        for element in script:
            index = element.get('index')

            if self.indices_to_process is not None and index not in self.indices_to_process:
                self.logger.debug(f"Skipping index {index} as it's not in the provided indices.")
                continue

            caption = element.get('caption')
            prompt = element.get('prompt')
            voiceover = element.get('voiceover', caption)
            is_video = element.get('is_video', True)

            try:
                # 1. Generate audio
                self.audio_generator.generate_audio(
                    caption=voiceover,
                    output_audio_path=f"{self.working_dir}/{index}.wav"
                )

                if is_video:
                    # 2a. Generate video
                    self.video_generator.generate_video(
                        prompt=prompt,
                        index=index,
                        output_video_path=f"{self.working_dir}/{index}.mp4"
                    )

                    # 2b. Interpolate video
                    self.interpolator.interpolate(
                        input_video_path=f"{self.working_dir}/{index}.mp4",
                        output_video_path=f"{self.working_dir}/{index}_interpolated.mp4"
                    )
                else:
                    # 2. Generate freeze frame video
                    self.freeze_video_generator.generate_freeze_video(
                        prompt=prompt,
                        index=index,
                        output_video_path=f"{self.working_dir}/{index}_interpolated.mp4",
                    )

                # 3. Add audio and caption to video
                self.captioner.add_audio_and_caption(
                    caption=caption,
                    audio_path=f"{self.working_dir}/{index}.wav",
                    input_video_path=f"{self.working_dir}/{index}_interpolated.mp4",
                    output_video_path=f"{self.working_dir}/{index}_captioned.mp4"
                )

                self.logger.info(f"Successfully processed iteration with index={index}")
            except Exception:
                self.logger.error(f"Error processing iteration with index={index}: \n{print(traceback.format_exc())}")
                self.failed_indices.append(index)

        if not failed_indices:
            self.logger.info("All iterations completed successfully!")

            try:
                # 4. Concatenate videos
                self.concatenator.concatenate_videos()
                    
                # 5a. Generate background music if not provided
                if music and self.existed_music_path is None:
                    self.bg_music_adder.generate_music(music, f"{self.working_dir}/music.wav")
                    self.existed_music_path = f"{self.working_dir}/music.wav"
            
                # 5b. Add background music
                self.bg_music_adder.add_background_music(
                input_video_path=f"{self.working_dir}/concat.mp4",
                music_path=self.existed_music_path,
                output_video_path=f"{self.working_dir}.mp4"
                )

                self.logger.info(f"Final video successfully saved to: {self.working_dir}.mp4")
            except Exception:
                self.logger.error(f"Error during concatenation or adding background music: \n{print(traceback.format_exc())}")

        else:
            self.logger.warning("Some iterations failed. concat.py will not be run.")
            self.logger.warning(f"Failed iterations: {failed_indices}")

def main():
    parser = argparse.ArgumentParser(description="Process JSON data to generate YouTube videos.")
    parser.add_argument("-j", "--json_file", default="inputs/AI_YouTuber/scripts/News_trump_ditches_penny.json", help="Path to the JSON file.")
    parser.add_argument("-w", "--working_dir", default="outputs/HunYuan/20250211_News_trump_ditches_penny", help="Working directory for output files.")
    parser.add_argument("-m", "--music_path", default="inputs/AI_YouTuber/music/News.m4a", help="Path to the background music file.")
    parser.add_argument("-i", "--indices", nargs='+', type=int, help="List of indices to process. If not provided, all indices will be processed.")
    parser.add_argument("-l", "--log_level", default="INFO", help="Logging level (e.g., DEBUG, INFO, WARNING, ERROR)")
    args = parser.parse_args()

    # Set up logging
    log_level = getattr(logging, args.log_level.upper(), None)
    if not isinstance(log_level, int):
        raise ValueError('Invalid log level: %s' % args.log_level)
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    json_file = args.json_file
    working_dir = args.working_dir
    music_path = args.music_path
    indices_to_process = args.indices

    shorts_maker = YTShortsMaker(json_file, working_dir, music_path, indices_to_process, logger)
    shorts_maker.run()

if __name__ == "__main__":
    main()