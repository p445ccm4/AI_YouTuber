import json
import os

def update_proposals_titles(titles_json_file, proposals_dir="."):
    """
    Updates the titles in existing proposal JSON files based on a titles JSON file.

    Args:
        titles_json_file (str): Path to the JSON file containing titles.
        proposals_dir (str, optional): Directory containing proposal JSON files. Defaults to current directory.
    """

    try:
        with open(titles_json_file, 'r') as f:
            titles_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Titles JSON file not found: {titles_json_file}")
        return
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in titles file: {titles_json_file}")
        return

    for filename_key, title_values in titles_data.items():
        proposal_filename = f"{filename_key}.json" # Reconstruct filename based on key. Adjust if your naming is different.
        proposal_filepath = os.path.join(proposals_dir, proposal_filename)

        if not os.path.exists(proposal_filepath):
            print(f"Warning: Proposal file not found: {proposal_filepath}")
            continue

        try:
            with open(proposal_filepath, 'r') as f:
                proposal_data = json.load(f)
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON format in proposal file: {proposal_filepath}")
            continue

        if "thumbnail" not in proposal_data:
            proposal_data["thumbnail"] = {}

        proposal_data["thumbnail"]["short_title"] = title_values["short_title"]
        proposal_data["thumbnail"]["long_title"] = title_values["long_title"]
        if "title" in proposal_data["thumbnail"]:
            del proposal_data["thumbnail"]["title"] # Remove the old title key

        try:
            with open(proposal_filepath, 'w') as f:
                json.dump(proposal_data, f, indent=2) # Save with indentation for readability
            print(f"Updated titles in: {proposal_filepath}")
        except IOError:
            print(f"Error: Could not write to proposal file: {proposal_filepath}")

if __name__ == "__main__":
    titles_file = "inputs/MBTI_mad_corrections.json" # Replace with the actual filename of your titles json file
    proposals_directory = "inputs/proposals" # Replace with the actual directory if your proposal files are in a subfolder.

    update_proposals_titles(titles_file, proposals_directory)
    print("Title update process completed.")