from openai import AsyncAzureOpenAI, AsyncOpenAI

# Function to define and return the LLM configurations
def get_llm_configurations():
    # Central dictionary to hold all your LLM configurations
    # Each value is a dictionary containing the necessary parameters for client initialization
    llm_configs = {}

    # Azure OpenAI setup
    with open("inputs/OpenAI_API.txt", "r") as f:
        llm_configs["o4-mini"] = {
            "model": "o4-mini",
            "base_url": "https://successbaseopenai.openai.azure.com/",
            "api_key": f.read().strip(),
            "api_version": "2024-12-01-preview",
            "client_class": AsyncAzureOpenAI
        }

    # Local Qwen3
    llm_configs["qwen3:32b"] = {
        "model": "qwen3:32b",
        "base_url": 'http://localhost:11434/v1',
        "api_key": 'ollama',
        "client_class": AsyncOpenAI
    }

    # Gemini 2.5 Flash
    with open("inputs/Gemini_API.txt", "r") as f:
        llm_configs["gemini-2.5-flash"] = {
            "model": "gemini-2.5-flash",
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
            "api_key": f.read().strip(),
            "client_class": AsyncOpenAI
        }

    # DeepSeek V3
    with open("inputs/DeepSeek_API.txt", "r") as f:
        llm_configs["deepseek-chat"] = {
            "model": "deepseek-chat",
            "base_url": "https://api.deepseek.com/v1",
            "api_key": f.read().strip(),
            "client_class": AsyncOpenAI
        }

    return llm_configs

# Global access to configurations (or pass it around if you prefer)
LLM_CONFIGS = get_llm_configurations()

async def gen_response(user_message: str, history: list[dict], model_name: str, system_prompt: str = "", stream=True):
    # Retrieve the LLM configuration dictionary
    if not (llm_config := LLM_CONFIGS.get(model_name)):
        raise ValueError(f"Model '{model_name}' not found in configurations.")

    # Initialize the appropriate client based on the client_class in the config
    client_class = llm_config["client_class"]
    if client_class == AsyncAzureOpenAI:
        client = client_class(
            azure_endpoint=llm_config["base_url"],
            api_key=llm_config["api_key"],
            api_version=llm_config.get("api_version") # Use .get() for optional keys
        )
    elif client_class == AsyncOpenAI:
        client = client_class(
            base_url=llm_config["base_url"],
            api_key=llm_config["api_key"]
        )
    else:
        raise TypeError(f"Unsupported client class: {client_class}")

    # Handle User Text Input
    if user_message:
        history.append(
            {
                "role": "user",
                "content": user_message
            }
        )

    # Handle System Prompt
    if system_prompt:
        if not history or history[0]["role"] != "system":
            history.insert(0, {"role": "system", "content": system_prompt})
        else:
            history[0] = {"role": "system", "content": system_prompt}

    if stream:
        response = ""
        stream_resp = await client.chat.completions.create(
            model=model_name,
            messages=history,
            stream=True,
        )
        async for chunk in stream_resp:
            delta = chunk.choices[0].delta.content or ""
            response += delta
            yield response
    else:
        resp = await client.chat.completions.create(
            model=model_name,
            messages=history,
            stream=False,
        )
        yield resp.choices[0].message.content

def get_model_names():
    return list(LLM_CONFIGS.keys())