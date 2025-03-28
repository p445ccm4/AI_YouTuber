import ollama

def gen_response(user_message:str, history:list[dict], ollama_model:str, system_prompt:str=""):
    text_input = []
    
    # Handle User Text Input
    if user_message:
        text_input.append(f"User Input: {user_message}")
        history.append(
            {
                "role": "user",
                "content": "\n\n".join(text_input)
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