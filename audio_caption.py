import argparse
import moviepy
import logging
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
import json
import llm

class VideoCaptioner:
    def __init__(self, make_shorts, llm_model, logger):
        self.make_shorts = make_shorts
        self.logger = logger
        self.pipe = None
        self.ollama_model = llm_model

    def _load_model(self):
        if not self.pipe:
            self.logger.info("Loading Whisper model...")
            model_id = "./models/whisper-large-v3-turbo"
            model = AutoModelForSpeechSeq2Seq.from_pretrained(
                model_id, use_safetensors=True
            ).to("cpu")
            processor = AutoProcessor.from_pretrained(model_id)
            self.pipe = pipeline(
                "automatic-speech-recognition",
                model=model,
                tokenizer=processor.tokenizer,
                feature_extractor=processor.feature_extractor,
                device="cuda",
            )
            self.logger.info("Whisper model loaded.")

    async def get_audio_timestamp(self, caption, input_audio_path):
        """Return (True, Timed Caption) if the transcription is matched with caption or saved by LLM."""
        # Whisper inference
        self._load_model()
        self.pipe.model.to("cuda")
        try:
            timed_caption = self.pipe(
                input_audio_path, 
                return_timestamps="word",
                generate_kwargs={
                    "language": "english",
                }
            )
        except Exception as e:
            self.logger.error(f"Audio Caption has error: {e}")
            raise e
        finally:
            self.pipe.model.to("cpu")

        transcription_alnum = ''.join(e for e in timed_caption["text"] if e.isalnum()).lower()
        caption_alnum = ''.join(e for e in caption if e.isalnum()).lower()
        if transcription_alnum != caption_alnum:
            # Ask DeepSeek if the transcription is not matched with caption
            with open("inputs/System_Prompt_Timed_Transcription.txt", "r") as f:
                system_prompt = f.read()
            message = json.dumps(
                            {
                            "script": caption,
                            "timed_caption": timed_caption
                            }
            )
            
            async for r in llm.gen_response(message, [], self.ollama_model, system_prompt, stream=False):
                response = r
            _, _, response = response.rpartition("</think>")
            response = response.strip()
            
            comparison = f"\nTranscription:\t{timed_caption["text"]}\nCaption:\t{caption}\nLLM Response:\t{response}"
            self.logger.info(comparison)
            if response.startswith("modified"):
                try:
                    timed_caption = json.loads(response.removeprefix("modified ").strip())
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse modified JSON")
                    raise e
            else:
                return False, comparison
        
        return self.check_timed_caption(timed_caption, input_audio_path)

    @staticmethod
    def check_timed_caption(timed_caption, input_audio_path):
        audio_duration = moviepy.AudioFileClip(input_audio_path).duration
        if any(chunk["timestamp"][0] > audio_duration for chunk in timed_caption["chunks"]):
            return False, f"Modified caption has wrong timestamp: {timed_caption}"
        else:
            return True, timed_caption

    def add_audio_and_caption_tiktok_style(self, timed_caption, input_video_path, input_audio_path, output_video_path):
        # Load video and audio
        video_clip = moviepy.VideoFileClip(input_video_path)
        audio_clip = moviepy.AudioFileClip(input_audio_path)

        # Create text clips for each chunk
        text_clips = []
        current_batch_text, current_batch_duration, current_batch_start = [], 0.0, 0.0
        for chunk in timed_caption["chunks"]:
            text = chunk["text"]
            start, end = chunk["timestamp"]
            if not end:
                end = video_clip.duration
            current_batch_text.append(text)
            current_batch_duration += end - start
            if current_batch_duration < 0.3 and end != video_clip.duration:
                continue

            text_clip = (
                moviepy.TextClip(
                    font="Chilanka-Regular", 
                    text=" ".join(current_batch_text), 
                    method="caption",
                    size=(video_clip.w - 200, video_clip.h - 200),
                    margin=(200, 200),
                    font_size=75 if self.make_shorts else 50, 
                    color="white", 
                    bg_color=None,
                    stroke_color="black", 
                    stroke_width=3,
                    text_align="center",
                    vertical_align="top" if self.make_shorts else "bottom",
                )
                .with_position(("center", "top") if self.make_shorts else ("center", "bottom"))
                .with_duration(current_batch_duration)
                .with_start(current_batch_start)
            )
            text_clips.append(text_clip)

            current_batch_start += current_batch_duration
            current_batch_text, current_batch_duration = [], 0.0

        # Combine video with all text clips
        final_clip = moviepy.CompositeVideoClip([video_clip] + text_clips)

        # Add audio to the video
        final_clip = final_clip.with_audio(audio_clip.with_effects([moviepy.afx.AudioNormalize()]))

        # Write the output video file
        final_clip.write_videofile(output_video_path, ffmpeg_params=["-hide_banner", "-loglevel", "error"])

        self.logger.info(f"Successfully added timed captions to video: {output_video_path}")

    def add_audio_and_caption(self, input_video_path, output_video_path, caption=None, input_audio_path=None, title=False):
        # Load video
        video_clip = moviepy.VideoFileClip(input_video_path)

        # Add caption if provided
        if caption:
            font_size = 120 if title else 50
            stroke_width = 5 if title else 3
            position = ("center", "center") if title else ("center", "top")
            vertical_align = "center" if title else "top"
            text_clip = (
                moviepy.TextClip(
                    font="Chilanka-Regular", 
                    text=caption, 
                    method="caption",
                    size=(video_clip.w - 200, video_clip.h - 200),
                    margin=(200, 200),
                    font_size=font_size, 
                    color="white", 
                    bg_color=None,
                    stroke_color="black", 
                    stroke_width=stroke_width,
                    text_align="center",
                    vertical_align=vertical_align,
                )
                .with_position(position)
                .with_duration(video_clip.duration)
            )
            video_clip = moviepy.CompositeVideoClip(clips=[video_clip, text_clip])

        # Add audio if provided
        if input_audio_path:
            audio_clip = moviepy.AudioFileClip(input_audio_path).with_effects([moviepy.afx.AudioNormalize()])
            video_clip.without_audio()
            video_clip = video_clip.with_audio(audio_clip)
        
        # Write the output video file
        video_clip.write_videofile(output_video_path, ffmpeg_params=["-hide_banner", "-loglevel", "error"])

        # Save the thumbnail
        if title:
            video_clip.save_frame(output_video_path.replace(".mp4", ".png"), t=0, with_mask=False)
        
        self.logger.info(f"Successfully added audio and caption to video: {output_video_path}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    parser = argparse.ArgumentParser(description="Add audio and caption to a video.")
    parser.add_argument("--input_audio_path", type=str, help="Path to the audio file", required=False)
    parser.add_argument("--caption", type=str, help="Caption text to add to the video", required=False)
    parser.add_argument("--input_video_path", type=str, help="Path to the input video file")
    parser.add_argument("--output_video_path", type=str, help="Path to the output video file")
    parser.add_argument("--title", action="store_true", help="If set, the text will be added to the center of the video with font size 80")
    
    args = parser.parse_args()
    
    captioner = VideoCaptioner(logger=logger)
    
    # captioner.add_audio_and_caption(
    #     input_audio_path=args.input_audio_path,
    #     input_video_path=args.input_video_path,
    #     output_video_path=args.output_video_path,
    #     caption=args.caption,
    #     title=args.title,
    # )

    captioner.add_audio_and_caption_tiktok_style(
        input_audio_path=args.input_audio_path,
        input_video_path=args.input_video_path,
        output_video_path=args.output_video_path,
    )