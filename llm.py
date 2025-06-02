import ollama

OLLAMA_CLIENT = ollama.Client()

def gen_response(user_message:str, history:list[dict], ollama_model:str, system_prompt:str="", stream=True, keep_alive=None):
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
        for chunk in OLLAMA_CLIENT.chat(
            model=ollama_model, 
            messages=history, 
            stream=True,
            keep_alive=keep_alive
        ):
            response += chunk['message']['content']

            yield response
    else:
        response = OLLAMA_CLIENT.chat(
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
    model_list = ollama.list().get("models")
    return [m['model'] for m in model_list]