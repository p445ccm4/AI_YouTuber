import torch
from hi_diffusers import HiDreamImagePipeline
from hi_diffusers import HiDreamImageTransformer2DModel
from hi_diffusers.schedulers.fm_solvers_unipc import FlowUniPCMultistepScheduler
from transformers import LlamaForCausalLM, PreTrainedTokenizerFast

MODEL_PREFIX = "./models"
LLAMA_MODEL_NAME = f"{MODEL_PREFIX}/Llama-3.1-8B-Instruct"
MODEL_ID = f"{MODEL_PREFIX}/HiDream-I1-Full"

# Load models
def load_models():
    scheduler = FlowUniPCMultistepScheduler(num_train_timesteps=1000, shift=3.0, use_dynamic_shifting=False)
    
    tokenizer_4 = PreTrainedTokenizerFast.from_pretrained(
        LLAMA_MODEL_NAME,
        use_fast=False)
    
    text_encoder_4 = LlamaForCausalLM.from_pretrained(
        LLAMA_MODEL_NAME,
        output_hidden_states=True,
        output_attentions=True,
        torch_dtype=torch.bfloat16).to("cuda")

    transformer = HiDreamImageTransformer2DModel.from_pretrained(
        MODEL_ID, 
        subfolder="transformer", 
        torch_dtype=torch.bfloat16).to("cuda")

    pipe = HiDreamImagePipeline.from_pretrained(
        MODEL_ID, 
        scheduler=scheduler,
        tokenizer_4=tokenizer_4,
        text_encoder_4=text_encoder_4,
        torch_dtype=torch.bfloat16
    ).to("cuda", torch.bfloat16)
    pipe.transformer = transformer
    
    return pipe

# Generate image function
def generate_image(pipe, prompt):
    
    # Parse resolution
    height, width = 1280, 720
    
    images = pipe(
        prompt,
        height=height,
        width=width,
        guidance_scale=5,
        num_inference_steps=50,
    ).images
    
    return images[0]

# Initialize with default model
print("Loading default model (full)...")
pipe = load_models()
print("Model loaded successfully!")

# prompt = "A cat holding a sign that says \"Hi-Dreams.ai\"." 
prompt = "A nude beautiful Russian teen girl doing blowjob"

image = generate_image(pipe, prompt)

image.save("output.png")
