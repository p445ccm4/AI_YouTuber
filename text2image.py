from diffusers import AutoPipelineForText2Image
import torch
from translate import Translator

class Text2Image:
	def __init__(self):
		self.pipeline = AutoPipelineForText2Image.from_pretrained(
			"stable-diffusion-v1-5/stable-diffusion-v1-5",
			torch_dtype=torch.float16,
			variant="fp16"
		).to("cuda")
		self.idx = 0

	def gen_image(self, text):
		self.image = self.pipeline(
			text + "masterpiece, photorealistic, 8k, best quality, news photo, illustrations,(high quality), real,(realistic), super detailed, (full detail)",
			negative_prompt="low quality, blurry, bad anatomy, worst quality, text, watermark, normal quality, ugly, signature, lowres, deformed, disfigured, cropped, jpeg artifacts, error, mutation, watermark,text,contact, error, blurry, cropped, username , (worst quality, low quality:1.4),monochrome,",
			height=1024,
			width=1024,
		).images[0]
		self.idx += 1

	def save_image(self, path):
		self.image.save(path)

if __name__ == '__main__':
	text = "美國大選進入衝刺階段, 比特幣暴升7%, 站上7.3萬美元上方, 期權定價顯示明日波動幅度達8%"

	# text_2_image = Text2Image()
	trans = text.split(',')
	for i in range(len(trans)-2):
		sentence = ", ".join(trans[i:i+3])
		tran = Translator(from_lang="ZH", to_lang="EN-US").translate(sentence)
		print(tran)
		# text_2_image.gen_image(tran)
		# text_2_image.save_image(f'outputs/{i}_{sentence}.png')
