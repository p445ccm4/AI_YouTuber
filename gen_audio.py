import argparse
import os
import logging
import torchaudio
from zonos.model import Zonos
from zonos.conditioning import make_cond_dict
from zonos.utils import DEFAULT_DEVICE as device
from chatterbox.tts import ChatterboxTTS

class AudioGenerator:
    def __init__(self, logger=None, zonos_model_path="./models/Zonos-v0.1-hybrid", reference_audio_path=""):
        self.logger = logger
        # self.zonos_model_path = zonos_model_path
        self.chatterbox_model_path = "./models/chatterbox"
        self.reference_audio_path = reference_audio_path
        # self.speaker_embedding = None
        self.model = None

    def _load_model(self):
        if self.model is None:
            # self.logger.info("Loading Zonos model...")
            # config_path = os.path.join(self.zonos_model_path, "config.json")
            # model_path = os.path.join(self.zonos_model_path, "model.safetensors")
            # self.model = Zonos.from_local(config_path, model_path, device=device).to('cpu')
            # self.model.eval()  # Set the model to evaluation mode

            self.model = ChatterboxTTS.from_local(self.chatterbox_model_path, device="cuda")
        self._chatterbox_to('cpu')

        # if self.speaker_embedding is None and self.reference_audio_path:
        #     self.logger.info("Making speaker embedding...")
        #     wav, sr = torchaudio.load(self.reference_audio_path)
        #     self.model.to(device)
        #     self.speaker_embedding = self.model.make_speaker_embedding(wav, sr)
        #     self.model.to('cpu')

    def _chatterbox_to(self, device):
        self.model.ve = self.model.ve.to(device)
        self.model.t3 = self.model.t3.to(device)
        self.model.s3gen = self.model.s3gen.to(device)
        self.model.conds = self.model.conds.to(device) if self.model.conds else None

    def generate_audio(self, caption, output_audio_path, speaking_rate=15):
        if os.path.exists(output_audio_path):
            os.remove(output_audio_path)
        assert caption != "" and caption is not None, "Caption/Voiceover cannot be empty."

        self._load_model() # Load model here

        # Generate audio with Zonos
        # self.model.to(device)
        # cond_dict = make_cond_dict(text=caption,
        #                            speaker=self.speaker_embedding, 
        #                            language="en-us",
        #                            speaking_rate=speaking_rate,
        #                            emotion=[0.0256, 0.0256, 0.0256, 0.0256, 0.0256, 0.9, 0.0256, 0.0256],
        #                            # Happiness, Sadness, Disgust, Fear, Surprise, Anger, Other, Neutral
        #                            )
        # conditioning = self.model.prepare_conditioning(cond_dict)
        # codes = self.model.generate(conditioning)
        # wav = self.model.autoencoder.decode(codes).cpu()[0]
        # torchaudio.save(output_audio_path, wav, self.model.autoencoder.sampling_rate)
        # self.logger.info(f"Zonos generated audio: {output_audio_path}")

        # if self.speaker_embedding is None:
        #     self.speaker_embedding = self.model.make_speaker_embedding(wav, self.model.autoencoder.sampling_rate)

        # self.model.to('cpu')

        self._chatterbox_to('cuda')
        wav = self.model.generate(
            text=caption,
            audio_prompt_path=self.reference_audio_path,
            exaggeration=0.7,
            cfg_weight=0.3
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