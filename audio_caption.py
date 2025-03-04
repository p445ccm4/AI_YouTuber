import argparse
import os
import moviepy
import logging
import whisper_timestamped as whisper

class VideoCaptioner:
    def __init__(self, logger=None):
        self.logger = logger
        self.whisper_model = None

    def add_caption_tiktok_style(self, input_video_path, output_video_path):
        #TODO https://github.com/linto-ai/whisper-timestamped?tab=readme-ov-file#example-output
        if not self.model:
            self.model = whisper.load_model("./models/whisper-large-v2-nob", device="cpu")

        audio = whisper.load_audio("AUDIO.wav")
        self.model.to('cuda')
        result = whisper.transcribe(self.model, audio, language="en")
        #TODO: add caption word by word

    def add_audio_and_caption(self, input_video_path, output_video_path, caption=None, audio_path=None, title=False):
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
        if audio_path:
            audio_clip = moviepy.AudioFileClip(audio_path).with_effects([moviepy.afx.AudioNormalize()])
            video_clip.without_audio()
            video_clip = video_clip.with_audio(audio_clip)
        
        # Write the output video file
        video_clip.write_videofile(output_video_path, ffmpeg_params=["-hide_banner", "-loglevel", "error"])

        # Delete the original video
        # os.remove(input_video_path)
        
        self.logger.info(f"Successfully added audio and caption to video: {output_video_path}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    parser = argparse.ArgumentParser(description="Add audio and caption to a video.")
    parser.add_argument("--audio_path", type=str, help="Path to the audio file", required=False)
    parser.add_argument("--caption", type=str, help="Caption text to add to the video", required=False)
    parser.add_argument("--input_video_path", type=str, help="Path to the input video file")
    parser.add_argument("--output_video_path", type=str, help="Path to the output video file")
    parser.add_argument("--title", action="store_true", help="If set, the text will be added to the center of the video with font size 80")
    
    args = parser.parse_args()
    
    captioner = VideoCaptioner()
    
    captioner.add_audio_and_caption(
        audio_path=args.audio_path,
        input_video_path=args.input_video_path,
        output_video_path=args.output_video_path,
        caption=args.caption,
        title=args.title
    )
