import json
import os

def print_titles(folder_path="inputs/proposals"):
    """Reads JSON proposal files from a folder and returns the long titles as a string."""
    output_string = "" # Capture output in a string
    for filename in sorted(os.listdir(folder_path)):
        if filename.startswith("") and filename.endswith(".json"):
            filepath = os.path.join(folder_path, filename)
            with open(filepath, 'r') as f:
                try:
                    proposal_data = json.load(f)
                    long_title = proposal_data.get("thumbnail", {}).get("long_title")
                    if long_title:
                        output_string += f"{filename}: {long_title}\n"
                    else:
                        output_string += f"Warning: No long title found in {filename}\n"
                except json.JSONDecodeError:
                    output_string += f"Error: Could not decode JSON in {filename}\n"
    return output_string # Return the output string


# if __name__ == "__main__": # Remove this block for import
#     folder_path = "inputs/proposals"
#     print_titles(folder_path)