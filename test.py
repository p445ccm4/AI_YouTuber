from transformers import AutoProcessor, ShieldGemmaForImageClassification
from PIL import Image
import requests
import torch

model_id = "models/shieldgemma-2-4b-it"

image = Image.open("outputs/20250306_MBTI_TvsF_5_revised/-1_captioned.png")

model = ShieldGemmaForImageClassification.from_pretrained(model_id).eval()
processor = AutoProcessor.from_pretrained(model_id)

model_inputs = processor(images=[image], return_tensors="pt")

with torch.inference_mode():
    scores = model(**model_inputs)

print(scores.probabilities)
