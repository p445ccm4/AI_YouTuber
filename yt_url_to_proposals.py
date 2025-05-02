import subprocess
from youtube_transcript_api import YouTubeTranscriptApi
import google
import os

ytt_api = YouTubeTranscriptApi()
# --- Configuration ---
# Define the path for the script file (consistent between functions)
SCRIPT_DIR = "inputs/proposals"
SCRIPT_FILENAME = "ZZZ_write_proposals.py"
SCRIPT_FULL_PATH = os.path.join(SCRIPT_DIR, SCRIPT_FILENAME)

def get_transcripts(yt_url:str):
    video_id = yt_url.split("watch?v=")[-1].split("&")[0]

    transctips = ytt_api.fetch(video_id, languages=['en', 'zh-Hant', 'zh-Hans'])

    return " ".join([snippet.text for snippet in transctips])

def get_write_proposal_py(transcription:str, series:str, start_index:int|str) -> str:
    start_index = int(start_index)
    with open("inputs/System_Prompt_Proposal.txt", "r") as f:
        system_prompt = f.read()
    
    with open("inputs/Gemini_API.txt", "r") as f:
        GEMINI_API_KEY = f.read().strip()
        client = google.genai.Client(api_key=GEMINI_API_KEY)

    response = client.models.generate_content(
        model="gemini-2.5-flash-preview-04-17",
        config=google.genai.types.GenerateContentConfig(
            system_instruction=system_prompt),
        contents=[f"""
                  Make multiple proposals to cover the whole script. Put them into one single python script to save them into "inputs/proposals/{series}_{start_index}.json", "inputs/proposals/{series}_{start_index+1}.json" and so on. Print the base filenames at the end without printing extension ".json". 
                  Script:
                  {transcription}
                  """]
    )

    #TODO: truncate thoughts from response?
    # Write the content to the file
    with open(SCRIPT_FULL_PATH, "w") as f:
        f.write(response.text)
    return f"Successfully wrote script content to {SCRIPT_FULL_PATH}.\n"

def write_proposals_and_make_topics_file(output_topics_path: str):
    """
    Runs the ZZZ_write_proposals.py script using 'python' command,
    captures its stdout and stderr, and appends them to the specified
    output file.

    Args:
        output_filepath: The path to the file where the script's output
                         should be appended.
    """
    # Command to execute the script
    command = ["python", SCRIPT_FULL_PATH]
    # Run the command
    result = subprocess.run(
        command,
        check=True,         # Raise CalledProcessError if command returns non-zero exit code
        capture_output=True,# Capture standard output and error
        text=True           # Decode output/error as text using default encoding
        # No cwd is specified here because 'python inputs/proposals/ZZZ_write_proposals.py'
        # is executed relative to the directory where *this* script is run.
        # If you needed to run 'python ZZZ_write_proposals.py' *from* the inputs/proposals dir,
        # you would use: command = ["python", SCRIPT_FILENAME], cwd=SCRIPT_DIR
    )
    yield "Script executed successfully."

    # Prepare output to append
    output_to_append = f"\n--- Output from {SCRIPT_FULL_PATH} ---\n"
    if result.stdout:
        output_to_append += f"--- STDOUT ---\n{result.stdout}\n"
    if result.stderr:
            # Note: Some tools write warnings/info to stderr even on success
        output_to_append += f"--- STDERR ---\n{result.stderr}\n"
    output_to_append += f"--- End Output ---\n"

    # Append output to the specified file
    with open(output_topics_path, "a") as f:
        f.write(output_to_append)

    return f"Successfully appended topics to '{output_topics_path}'. Refresh the page to see changes.\n"

def make_proposals(yt_urls:str, output_topics_path:str, series:str, start_index:int|str):
    messages = "Start Generating... This may take a few minutes..."
    yield messages
    for yt_url in yt_urls.split("\n"):
        if not yt_url.strip() or yt_url.startswith("#"):
            continue
        
        # Only works when VPN is off
        video_transcription = get_transcripts(yt_url)
        # messages += f"Successfully get transcription from {yt_url}.\n"
        # yield messages

        # Only works when VPN is on
        # messages += get_write_proposal_py(video_transcription, series, start_index)
        # yield messages

        # messages += write_proposals_and_make_topics_file(output_topics_path)
        # yield messages

        yield video_transcription