import numpy as np
import torch
import moviepy
import argparse
import os
import logging
from PIL import Image
from io import BytesIO

class FreezeVideoGenerator:
    def __init__(self, make_shorts=True, logger=None):
        self.make_shorts = make_shorts
        self.logger = logger
        self.pipe = None  # Initialize pipe to None, model is not loaded yet

    def _load_model(self):
        if self.pipe is None: # Check if self.pipe is None
            self.logger.info("Loading FLUX model...")
            from diffusers import FluxPipeline
            self.pipe = FluxPipeline.from_pretrained("./models/FLUX.1-dev", torch_dtype=torch.bfloat16)
            self.pipe = self.pipe.to('cpu') # Load on CPU initially
            self.logger.info("FLUX model loaded.")

            # self.logger.info("Loading Hi-Dream model...")
            # from transformers import PreTrainedTokenizerFast, LlamaForCausalLM
            # from diffusers import HiDreamImagePipeline
            # tokenizer_4 = PreTrainedTokenizerFast.from_pretrained("./models/Llama-3.1-8B-Instruct")
            # text_encoder_4 = LlamaForCausalLM.from_pretrained(
            #     "./models/Llama-3.1-8B-Instruct",
            #     output_hidden_states=True,
            #     output_attentions=True,
            #     torch_dtype=torch.bfloat16,
            # )

            # self.pipe = HiDreamImagePipeline.from_pretrained(
            #     "./models/HiDream-I1-Full",
            #     tokenizer_4=tokenizer_4,
            #     text_encoder_4=text_encoder_4,
            #     torch_dtype=torch.bfloat16,
            # )

            # self.pipe = self.pipe.to('cpu')
            # self.pipe.enable_model_cpu_offload()
            # self.logger.info("Hi-Dream model loaded.")

    def generate_freeze_video(self, prompt, index, output_video_path, fps=20, num_frames=None):
        output_dir = os.path.dirname(output_video_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        if num_frames is None:
            if index != -1:
                audio_path = f"{output_dir}/{index}.wav"
                audio_clip = moviepy.AudioFileClip(audio_path)
                num_frames = audio_clip.duration * fps
                audio_clip.close()
            else:
                num_frames = 5 if self.make_shorts else 20 # For Thumbnail

        num_frames = int(num_frames // 4 * 4 + 1)
        duration = num_frames / fps
        height = 1280 if self.make_shorts else 720
        width = 720 if self.make_shorts else 1280

        self._load_model()
        self.pipe = self.pipe.to('cuda')
        output = self.pipe(
            prompt=prompt,
            height=height,
            width=width,
            num_inference_steps=40,
            guidance_scale=30.0,
        ).images[0]
        self.pipe = self.pipe.to('cpu')

        # Create a video clip from the frames
        clip = moviepy.ImageClip(np.array(output)).with_duration(duration)

        clip = self.make_random_effects(clip, width, height)

        # Write the video clip to a file
        clip.write_videofile(output_video_path, fps=fps)
        self.logger.info(f"Video saved to {output_video_path}")   

    def make_random_effects(self, clip:moviepy.VideoClip, width, height):
        effect = np.random.choice(["enlarge", "shrink", "scroll up", "scroll down", "scroll left", "scroll right"])

        if effect == "enlarge":
            effects = [moviepy.vfx.Resize(lambda t: 1 + 0.02*t)]
        elif effect == "shrink":
            effects = [moviepy.vfx.Resize(lambda t: 1.1 - 0.02*t)]
        elif effect == "scroll up":
            effects = [
                moviepy.vfx.Resize(1.1),
                moviepy.vfx.Scroll(w=width, h=height, y_speed=height*-0.02, y_start=int(height*0.1))
                ]
        elif effect == "scroll down":
            effects = [
                moviepy.vfx.Resize(1.1),
                moviepy.vfx.Scroll(w=width, h=height, y_speed=height*0.02)
                ]
        elif effect == "scroll left":
            effects = [
                moviepy.vfx.Resize(1.1),
                moviepy.vfx.Scroll(w=width, h=height, x_speed=width*-0.02, x_start=int(width*0.1))
                ]
        elif effect == "scroll right":
            effects = [
                moviepy.vfx.Resize(1.1),
                moviepy.vfx.Scroll(w=width, h=height, x_speed=width*0.02)
                ]
        
        clip = clip.with_effects(effects).with_background_color((width, height), (0, 0, 0), opacity=0)
        
        return clip

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(description="Generate videos from text prompts.")
    parser.add_argument("-i", "--index", type=int, required=True, help="Index of the prompt to process")
    parser.add_argument("-p", "--prompt", type=str, required=True, help="Prompt")
    parser.add_argument("-o", "--output_video_path", type=str, default="outputs/HunYuan/output.mp4", help="Output video path")
    parser.add_argument("-n", "--num_frames", type=int, default=None, help="Number of frames to generate")
    args = parser.parse_args()

    generator = FreezeVideoGenerator(logger)
    generator.generate_freeze_video(args.prompt, args.index, args.output_video_path, num_frames=args.num_frames)