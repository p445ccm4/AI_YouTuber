import os
import json
import argparse
import logging
import traceback
import gen_audio, gen_freeze_video, audio_caption, concat, gen_music, upload_YouTube # gen_video

class YTShortsMaker:
    def __init__(self, json_file, working_dir, indices_to_process=None, make_shorts=True, ollama_model="gemma3:27b", logger=None, upload=False):
        self.json_file = json_file
        self.working_dir = working_dir
        self.indices_to_process = indices_to_process
        self.logger:logging.Logger = logger
        # self.video_generator = gen_video.VideoGenerator(logger=self.logger)
        self.freeze_video_generator = gen_freeze_video.FreezeVideoGenerator(make_shorts=make_shorts, logger=self.logger)
        self.audio_captioner = audio_caption.VideoCaptioner(make_shorts=make_shorts, ollama_model=ollama_model, logger=self.logger)
        self.concatenator = concat.VideoConcatenator(self.working_dir, logger=self.logger)
        self.bg_music_adder = gen_music.MusicGenerator(logger=self.logger)
        self.yt_uploader = upload_YouTube.YouTubeUploader(logger=self.logger) if upload else None

        if "_women_" in json_file or "Zodiac_" in json_file or "MBTI_" in json_file:
            reference_audio_path = "inputs/reference_audio_woman.wav"
        # elif "Motivation_" in json_file:
        #     reference_audio_path = "inputs/reference_audio_man_30s.wav"
        else:
            # "_men_"
            reference_audio_path = "inputs/reference_audio_man.wav"
        self.audio_generator = gen_audio.AudioGenerator(logger=self.logger, reference_audio_path=reference_audio_path)

    def run(self):
        os.makedirs(self.working_dir, exist_ok=True)
        failed_idx_traceback = {}

        with open(self.json_file, 'r') as f:
            data = json.load(f)
            script = data.get('script', data.get('proposal'))
            thumbnail = data.get('thumbnail')
            music = data.get('music', None)
            short_title = thumbnail.get('short_title')
            prompt = thumbnail.get('prompt')
        
        if self.indices_to_process is not None and -1 not in self.indices_to_process:
            self.logger.debug(f"Skipping thumbnail generation as -1 is not in the provided indices.")
        else:
            try:
                yield
                # 1. Generate thumbnail
                self.freeze_video_generator.generate_freeze_video(
                    prompt=prompt,
                    index=-1,
                    output_video_path=f"{self.working_dir}/-1.mp4"
                )

                yield
                # 2. Add caption to thumbnail
                self.audio_captioner.add_audio_and_caption(
                    input_audio_path=None,
                    caption=short_title,
                    input_video_path=f"{self.working_dir}/-1.mp4",
                    output_video_path=f"{self.working_dir}/-1_captioned.mp4",
                    title=True
                )

                self.logger.info(f"Successfully processed thumbnail")
            except Exception as e:
                trace = traceback.format_exc()
                self.logger.error(f"Error processing thumbnail: \n{trace}")
                failed_idx_traceback["thumbnail"] = trace

        
        for element in script:
            index = element.get('index')
            if self.indices_to_process is not None and index not in self.indices_to_process:
                self.logger.debug(f"Skipping index {index} as it's not in the provided indices.")
                continue
            
            if os.path.exists(f"{self.working_dir}/{index}_captioned.mp4"):
                os.remove(f"{self.working_dir}/{index}_captioned.mp4")
            caption = element.get('caption')
            prompt = element.get('prompt')
            voiceover = element.get('voiceover', caption)

            try:
                speaking_rate = 20
                while True:
                    yield
                    # 3. Generate audio
                    self.audio_generator.generate_audio(
                        caption=voiceover,
                        output_audio_path=f"{self.working_dir}/{index}.wav",
                        speaking_rate=speaking_rate
                    )

                    yield
                    # 4. Get transcription
                    caption_matched, timed_caption = self.audio_captioner.get_audio_timestamp(
                        caption=caption,
                        input_audio_path=f"{self.working_dir}/{index}.wav"
                    )
                    if caption_matched:
                        self.logger.info(f"Successfully matched caption with speaking rate {speaking_rate}")
                        break
                    elif speaking_rate > 15:
                        # Generate slower audio if tiktok captioning is failed
                        self.logger.warn(f"""Failed to match caption with speaking rate {speaking_rate}.\nCaption comparison:
                                         {timed_caption}\nRetry audio with slower speaking rate...
                                         """)
                        speaking_rate -= 2
                        continue
                    else:
                        raise Exception(f"""
                                         Failed to match caption with speaking rate {speaking_rate}.\nCaption comparison:
                                         {timed_caption}
                                        """)

                yield
                # 5. Generate freeze video
                self.freeze_video_generator.generate_freeze_video(
                    prompt=prompt,
                    index=index,
                    output_video_path=f"{self.working_dir}/{index}.mp4",
                )

                yield
                # 6. Add audio and caption to video
                self.audio_captioner.add_audio_and_caption_tiktok_style(
                    timed_caption=timed_caption,
                    input_audio_path=f"{self.working_dir}/{index}.wav",
                    input_video_path=f"{self.working_dir}/{index}.mp4",
                    output_video_path=f"{self.working_dir}/{index}_captioned.mp4"
                )

                self.logger.info(f"Successfully processed iteration with index={index}")
                
            except Exception as e:
                trace = traceback.format_exc()
                self.logger.error(f"Error processing iteration with index={index}: \n{trace}")
                failed_idx_traceback[index] = trace

        if not failed_idx_traceback:
            self.logger.info("All iterations completed successfully!")

            try:
                yield
                # 7. Concatenate videos
                if self.indices_to_process is not None and -2 not in self.indices_to_process and os.path.exists(f"{self.working_dir}/concat.mp4"):
                    self.logger.warn(f"Skipping concat as -2 is not in the provided indices.")
                else:
                    self.concatenator.concatenate_videos()
                    
                yield
                # 8. Generate background music
                if self.indices_to_process is not None and -3 not in self.indices_to_process and os.path.exists(f"{self.working_dir}/music.wav"):
                    self.logger.debug(f"Skipping music generation as -3 is not in the provided indices.")
                else:
                    self.bg_music_adder.generate_music(
                        prompt=music, 
                        input_video_path=f"{self.working_dir}/concat.mp4",
                        output_audio_path=f"{self.working_dir}/music.wav")

                yield
                # 9. Add background music
                self.bg_music_adder.add_background_music(
                    input_video_path=f"{self.working_dir}/concat.mp4",
                    music_path=f"{self.working_dir}/music.wav",
                    output_video_path=f"{self.working_dir}/final.mp4"
                )

                if self.yt_uploader:
                    long_title = thumbnail.get('long_title')
                    description = data.get('description', "This content is made by me, HiLo World. All right reserved. Contact me if you want to use my content.")
                    tags = data.get('tags', None)
                    yield
                    # 10. Upload to YouTube
                    self.yt_uploader.upload_video(
                        input_video_path=f"{self.working_dir}/final.mp4",
                        input_thumbnail_path=f"{self.working_dir}/-1_captioned.png",
                        title=long_title,
                        publish_date=None,
                        description=description,
                        tags=tags,
                    )

                self.logger.info(f"{self.working_dir} successfully processed")
            except Exception as e:
                trace = traceback.format_exc()
                self.logger.error(f"Error during concatenation, adding background music or uploading to YouTube: \n{trace}")
                failed_idx_traceback["concat_music_youtube"] = trace
        
        if failed_idx_traceback:
            self.logger.error("Something failed. process may not be complete.")
            for index, trace in failed_idx_traceback.items():
                self.logger.error(f"Failed iteration {index}: \n{trace}")
            string_failed_idx_traceback = bytes(json.dumps(failed_idx_traceback, separators=(", \n", ": \n")), "utf-8").decode("unicode_escape")
            raise Exception(f"\nFailed iterations: \n{string_failed_idx_traceback}")

def main():
    parser = argparse.ArgumentParser(description="Process JSON data to generate YouTube videos.")
    parser.add_argument("-j", "--json_file", default="inputs/proposals/News_trump_ditches_penny.json", help="Path to the JSON file.")
    parser.add_argument("-w", "--working_dir", default="outputs/20250211_News_trump_ditches_penny", help="Working directory for output files.")
    parser.add_argument("-i", "--indices", nargs='+', type=int, help="List of indices to process. If not provided, all indices will be processed.")
    parser.add_argument("-l", "--log_level", default="ERROR", help="Logging level (e.g., DEBUG, INFO, WARNING, ERROR)")
    parser.add_argument("-u", "--upload", action="store_true", help="Upload video to YouTube")
    args = parser.parse_args()

    # Set up logging
    log_level = getattr(logging, args.log_level.upper(), None)
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    shorts_maker = YTShortsMaker(
        json_file=args.json_file, 
        working_dir=args.working_dir, 
        indices_to_process=args.indices, 
        logger=logger, 
        upload=args.upload
        )
    shorts_maker.run()

if __name__ == "__main__":
    main()