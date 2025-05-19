import torch
import soundfile as sf
from diffusers import StableAudioPipeline
import numpy as np

repo_id = "./models/stable-audio-open-1.0"
pipe = StableAudioPipeline.from_pretrained(repo_id, torch_dtype=torch.float16)
pipe = pipe.to("cuda")

# define the prompts
prompt = "The sound of a hammer hitting a wooden surface."
negative_prompt = "Low quality."

# set the seed for generator
generator = torch.Generator("cuda").manual_seed(0)

# run the generation
audio: torch.Tensor = pipe(
    prompt,
    negative_prompt=negative_prompt,
    num_inference_steps=1,
    audio_end_in_s=10.0,
    num_waveforms_per_prompt=2,
    generator=generator,
).audios

output = audio.float().cpu().numpy()

print(output.shape) # (2, 2, 441000)

output = output.transpose(0, 2, 1)
output = np.concatenate(output, axis=0)
sf.write("output.wav", output, pipe.vae.sampling_rate)