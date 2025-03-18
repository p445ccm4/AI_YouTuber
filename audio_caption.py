import argparse
import moviepy
import logging
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
from google import genai
from openai import OpenAI
import json

class VideoCaptioner:
    def __init__(self, logger:logging.Logger):
        self.logger = logger
        self.pipe = None
        with open("inputs/Gemini_API.txt", "r") as f:
            self.gemini_client = genai.Client(api_key=f.readline().strip())
        with open("inputs/DeepSeek_API.txt", "r") as f:
            self.client = OpenAI(api_key=f.readline().strip(), base_url="https://api.deepseek.com")

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

    def get_audio_timestamp(self, caption, input_audio_path):
        # Whisper inference
        self._load_model()
        self.pipe.model.to("cuda")
        timed_caption = self.pipe(
            input_audio_path, 
            return_timestamps="word",
            generate_kwargs={
                "language": "english",
            }
        )
        self.pipe.model.to("cpu")

        transcription_alnum = ''.join(e for e in timed_caption["text"] if e.isalnum()).lower()
        caption_alnum = ''.join(e for e in caption if e.isalnum()).lower()
        # Return True if the transcription is matched with caption
        if transcription_alnum == caption_alnum:
            return True, timed_caption
        else:
            # Ask DeepSeek if the transcription is not matched with caption
            response = self.client.chat.completions.create(
                model="deepseek-reasoner",
                messages=[
                    {
                        "role": "system", 
                        "content": """
                            I am a YouTube Shorts content creator. 
                            I am using a audio-to-text model to form word-level timed-transcription for the caption,
                            which means the model has returned the exact start and end time for each word I spoke in a audio.
                            However, the model is not accurate enough to fully detect what I am saying. 
                            I would like you to correct the words and add punctuations to the timed-transcription.
                            If the transcription is far away from the script, misses words or has extra words, answer me with "failed".
                            If the transcription has small problems with spelling, homophones or alias, 
                            answer me with "modified {...}", i.e. "modified" appeneded with your corrected dictionary.
                            Do not add other extra things nor changing the timestamp.
                            Answer me with "failed" if you are not certain.
                            Example input:
                            {
                                script: "INFJs are insightful and deeply caring.",
                                timed_caption: {"text": " NFJS are insightful and deeply caring.", "chunks": [{"text": " NFJS", "timestamp": (0.06, 0.62)}, {"text": " are", "timestamp": (0.62, 0.76)}, {"text": " insightful", "timestamp": (0.76, 1.22)}, {"text": " and", "timestamp": (1.22, 1.44)}, {"text": " deeply", "timestamp": (1.44, 1.74)}, {"text": " caring.", "timestamp": (1.74, None)}]}
                            }
                            Expected response:
                            "modified {"text": "INFJs are insightful and deeply caring.", "chunks": [{"text": "INFJs", "timestamp": (0.06, 0.62)}, {"text": " are", "timestamp": (0.62, 0.76)}, {"text": " insightful", "timestamp": (0.76, 1.22)}, {"text": " and", "timestamp": (1.22, 1.44)}, {"text": " deeply", "timestamp": (1.44, 1.74)}, {"text": " caring.", "timestamp": (1.74, None)}]}"
                        """
                    },
                    {
                        "role": "user",
                        "content": json.dumps(
                            {
                            "script": caption,
                            "timed_caption": timed_caption
                            }
                        )
                    },
                ],
                stream=False
            ).choices[0].message.content 
            
            comparison = f"\nTranscription:\t{timed_caption["text"]}\nCaption:\t{caption}\nDeepSeek Response:\t{response}"
            self.logger.debug(comparison)
            if response.startswith("modified"):
                return True, json.loads(response.removeprefix("modified "))
            else:
                return False, comparison

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
                    font_size=75, 
                    color="white", 
                    bg_color=None,
                    stroke_color="black", 
                    stroke_width=3,
                    text_align="center",
                    vertical_align="top",
                )
                .with_position(("center", "top"))
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

        # Delete the original video
        # os.remove(input_video_path)
        
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