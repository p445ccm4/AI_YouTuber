import subprocess
import argparse
import os
import logging

import torch
import torchaudio
from Zonos.zonos.model import Zonos
from Zonos.zonos.conditioning import make_cond_dict
from Zonos.zonos.utils import DEFAULT_DEVICE as device

class AudioGenerator:
    def __init__(self, logger=None, zonos_model_path="./models/Zonos-v0.1-transformer", reference_audio=None):
        self.logger = logger if logger else logging.getLogger(__name__)
        config_path = os.path.join(zonos_model_path, "config.json")
        model_path = os.path.join(zonos_model_path, "model.safetensors")
        self.model = Zonos.from_local(config_path, model_path, device=device).to('cpu')
        self.model.eval()  # Set the model to evaluation mode
        self.speaker_embedding = None

    def generate_audio(self, caption, output_audio_path, speed_factor=1.3):
        temp_audio_path = output_audio_path.replace(".wav", "_temp.wav")
        # Delete existing audio files if they exist
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
        if os.path.exists(output_audio_path):
            os.remove(output_audio_path)

        # Generate audio with Zonos
        self._generate_audio_with_zonos(caption, temp_audio_path)

        # Apply speed factor using ffmpeg
        self._speedup_and_normalize(temp_audio_path, output_audio_path, speed_factor)

        # Clean up temporary files
        os.remove(temp_audio_path)

        self.logger.info(f"Generated audio: {output_audio_path}")

    def _generate_audio_with_zonos(self, text, output_wav_path):
        self.model.to(device)
        cond_dict = make_cond_dict(text=text, speaker=self.speaker_embedding, language="en-us")
        conditioning = self.model.prepare_conditioning(cond_dict)
        codes = self.model.generate(conditioning)
        wav = self.model.autoencoder.decode(codes).cpu()[0]
        torchaudio.save(output_wav_path, wav, self.model.autoencoder.sampling_rate)
        self.logger.info(f"Zonos generated audio: {output_wav_path}")

        # Cache speaker embedding
        if self.speaker_embedding is None: 
            self.speaker_embedding = self.model.make_speaker_embedding(wav, self.model.autoencoder.sampling_rate)
        
        self.model.to('cpu')

    def _speedup_and_normalize(self, input_wav_path, output_wav_path, speed_factor):
        subprocess.call([
            "ffmpeg",
            "-hide_banner",
            "-loglevel", "error",
            "-i", input_wav_path,
            "-filter:a", f"atempo={speed_factor},loudnorm=I=-12:TP=-1.5:LRA=11",
            output_wav_path
        ])
        self.logger.info(f"Applied speed factor to: {output_wav_path}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(description="Generate videos from text prompts.")
    parser.add_argument("-c", "--caption", type=str, required=True, help="Caption")
    parser.add_argument("-o", "--output_audio_path", type=str, required=True, help="Output audio path")
    args = parser.parse_args()

    generator = AudioGenerator(logger)
    generator.generate_audio(args.c, args.o)
