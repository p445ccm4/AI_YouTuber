from rife_model import load_rife_model, rife_inference_with_latents
from diffusers.image_processor import VaeImageProcessor
from diffusers.utils import export_to_video
import torch
import torchvision
import argparse
import os
import logging

def sort_by_startint(a):
    return int(a.split("_")[0])

def split_sentence(prompt, max_length=100):
    result = []
    while len(prompt) > max_length:
        split_index = prompt.rfind(' ', 0, max_length)
        if split_index == -1:
            split_index = max_length
        result.append(prompt[:split_index])
        prompt = prompt[split_index + 1:]
    result.append(prompt)
    return '\n'.join(result)

class FrameInterpolator:
    def __init__(self, device='cuda', logger=None):
        model_path="./models/rife"
        self.device = device
        self.model = load_rife_model(model_path)
        self.logger = logger if logger else logging.getLogger(__name__)

    def interpolate(self, input_video_path, output_video_path):
        self.logger.info(f"Interpolating video: {input_video_path} -> {output_video_path}")
        # Read video
        video_frames, _, _ = torchvision.io.read_video(input_video_path)
        
        # Preprocess
        video_frames = video_frames.to(self.device) / 255.0
        video_frames = torch.permute(video_frames, (0, 3, 1, 2))
        video_frames = torch.unsqueeze(video_frames, 0)
        
        # Inference
        video_frames = rife_inference_with_latents(self.model, video_frames) # 5->10
        video_frames = rife_inference_with_latents(self.model, video_frames) # 10->20
        
        # Postprocess
        video_frames = VaeImageProcessor.pt_to_numpy(video_frames[0])
        
        # Export
        export_to_video(video_frames, output_video_path, fps=20)     

        # Delete the original video
        # os.remove(input_video_path)
        self.logger.info(f"Interpolation complete. Output saved to {output_video_path}")

def main():
    parser = argparse.ArgumentParser(description="Frame Interpolation")
    parser.add_argument("--input_video_path", type=str, help="Path to the input video")
    parser.add_argument("--output_video_path", type=str, help="Path to the output video")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    interpolator = FrameInterpolator(logger=logging.getLogger(__name__))
    interpolator.interpolate(args.input_video_path, args.output_video_path)

if __name__ == "__main__":
    main()