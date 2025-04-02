import ollama

def gen_response(user_message:str, history:list[dict], ollama_model:str, system_prompt:str=""):
    
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
    response = ""
    for chunk in ollama.chat(
        model=ollama_model, 
        messages=history, 
        stream=True
    ):
        response += chunk['message']['content']

        yield response