from ollama import AsyncClient

OLLAMA_CLIENT = AsyncClient()

async def gen_response(user_message:str, history:list[dict], ollama_model:str, system_prompt:str="", stream=True, keep_alive=None):
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
        if history[0]["role"] != "system":
            history.insert(0, {"role": "system", "content": system_prompt})
        else:
            history[0] = {"role": "system", "content": system_prompt}

    # Get response from LLM
    if stream:
        response = ""
        async for chunk in await OLLAMA_CLIENT.chat(
            model=ollama_model, 
            messages=history, 
            stream=True,
            keep_alive=keep_alive
        ):
            response += chunk['message']['content']

            yield response
    else:
        response = await OLLAMA_CLIENT.chat(
            model=ollama_model, 
            messages=history, 
            stream=False,
            keep_alive=keep_alive
        )
        yield response['message']['content']

def get_ollama_model_names():
    """
    Executes 'ollama list | tail -n +2 | cut -d' ' -f1' in Python.

    Returns:
        list: A list of model names, or an empty list if there's an error.
    """
    import subprocess
    ollama_process = subprocess.Popen(
        ['ollama', 'list'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    tail_process = subprocess.Popen(
        ['tail', '-n', '+2'],
        stdin=ollama_process.stdout,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    ollama_process.stdout.close() # Important to close to prevent deadlocks

    cut_process = subprocess.Popen(
        ['cut', '-d', ' ', '-f1'],
        stdin=tail_process.stdout,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    tail_process.stdout.close() # Important to close to prevent deadlocks

    stdout, stderr = cut_process.communicate()

    if cut_process.returncode != 0:
        print(f"Error running cut: {stderr}")
        return []

    model_names = [line.strip() for line in stdout.splitlines() if line.strip()]
    return model_names