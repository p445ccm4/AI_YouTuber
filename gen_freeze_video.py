import numpy as np
import torch
from diffusers import FluxPipeline
import moviepy
import argparse
import os
import logging

class FreezeVideoGenerator:
    def __init__(self, logger=None):
        self.logger = logger
        self.pipe = None  # Initialize pipe to None, model is not loaded yet

    def _load_model(self):
        if self.pipe is None: # Check if self.pipe is None
            self.logger.info("Loading FLUX model...")
            self.pipe = FluxPipeline.from_pretrained("./models/FLUX.1-dev", torch_dtype=torch.bfloat16)
            self.pipe = self.pipe.to('cpu') # Load on CPU initially
            self.logger.info("FLUX model loaded.")

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
                num_frames = 1 # For Thumbnail

        num_frames = int(num_frames // 4 * 4 + 1)
        self.logger.info(f"num_frames: {num_frames}")

        self._load_model() # Load model only when generate_freeze_video is called

        self.pipe = self.pipe.to('cuda') # Move model to GPU for generation
        output = self.pipe(
            prompt=prompt,
            height=1280,
            width=720,
            num_inference_steps=40,
            guidance_scale=30.0,
        ).images[0]
        self.pipe = self.pipe.to('cpu') # Move model back to CPU after generation to free GPU memory

        # Create a video clip from the frames
        clip = moviepy.ImageClip(np.array(output)).with_duration(num_frames / fps)

        # Write the video clip to a file
        clip.write_videofile(output_video_path, fps=fps)
        self.logger.info(f"Video saved to {output_video_path}")

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