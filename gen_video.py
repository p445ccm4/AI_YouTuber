import torch
from diffusers import HunyuanVideoTransformer3DModel, HunyuanVideoPipeline
from diffusers.utils import export_to_video
import moviepy
import argparse
import os
import logging

class VideoGenerator:
    def __init__(self, logger=None):
        self.logger = logger if logger else logging.getLogger(__name__)
        model_id = "./models/HunyuanVideo"
        self.transformer = HunyuanVideoTransformer3DModel.from_pretrained(
            model_id, subfolder="transformer", torch_dtype=torch.bfloat16
        )
        self.pipe = HunyuanVideoPipeline.from_pretrained(model_id, transformer=self.transformer, torch_dtype=torch.float16)
        self.pipe.vae.enable_tiling()
        self.pipe.enable_model_cpu_offload()

    def generate_video(self, prompt, index, output_video_path, fps=5, num_frames=None):
        output_dir = os.path.dirname(output_video_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        if num_frames is None:
            if index != -1:
                audio_path = f"{output_dir}/{index}.mp3"
                audio_clip = moviepy.AudioFileClip(audio_path)
                num_frames = audio_clip.duration * fps
            else:
                num_frames = 1 # For Thumbnail

        num_frames = int(num_frames // 4 * 4 + 1)
        self.logger.info(f"num_frames: {num_frames}")
        output = self.pipe(
            prompt=prompt,
            height=1280,
            width=720,
            num_frames=num_frames,
            num_inference_steps=40,
        ).frames[0]
        export_to_video(output, output_video_path, fps=fps)
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

    generator = VideoGenerator(logger)
    generator.generate_video(args.prompt, args.index, args.output_video_path, num_frames=args.num_frames)
