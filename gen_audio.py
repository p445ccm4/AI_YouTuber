import argparse
import os
import logging
import torchaudio
from chatterbox.tts import ChatterboxTTS

class AudioGenerator:
    def __init__(self, logger=None, chatterbox_model_path = "./models/chatterbox", reference_audio_path=""):
        self.logger = logger
        self.chatterbox_model_path = chatterbox_model_path
        self.reference_audio_path = reference_audio_path
        self.model = None

    def _load_model(self):
        if self.model is None:
            self.logger.info("Loading Chatterbox model...")
            self.model = ChatterboxTTS.from_local(self.chatterbox_model_path, device="cuda")
        self._chatterbox_to('cpu')

    def _chatterbox_to(self, device):
        self.model.ve = self.model.ve.to(device)
        self.model.t3 = self.model.t3.to(device)
        self.model.s3gen = self.model.s3gen.to(device)
        self.model.conds = self.model.conds.to(device) if self.model.conds else None

    def generate_audio(self, caption, output_audio_path, exaggeration_offset=0.2):
        if os.path.exists(output_audio_path):
            os.remove(output_audio_path)
        assert caption != "" and caption is not None, "Caption/Voiceover cannot be empty."

        self._load_model() # Load model here

        self._chatterbox_to('cuda')
        wav = self.model.generate(
            text=caption,
            audio_prompt_path=self.reference_audio_path,
            exaggeration=0.5+exaggeration_offset,
            cfg_weight=0.5-exaggeration_offset
        )
        self._chatterbox_to('cpu')
        torchaudio.save(output_audio_path, wav, self.model.sr)
        self.logger.info(f"Chatterbox generated audio: {output_audio_path}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(description="Generate videos from text prompts.")
    parser.add_argument("-c", "--caption", type=str, required=True, help="Caption")
    parser.add_argument("-o", "--output_audio_path", type=str, required=True, help="Output audio path")
    args = parser.parse_args()

    generator = AudioGenerator(logger)
    generator.generate_audio(args.c, args.o)