import subprocess
from youtube_transcript_api import YouTubeTranscriptApi
from llm import gen_response
import os

ytt_api = YouTubeTranscriptApi()
# --- Configuration ---
# Define the path for the script file (consistent between functions)
SCRIPT_DIR = "inputs/proposals"
SCRIPT_FILENAME = "ZZZ_write_proposals.py"
SCRIPT_FULL_PATH = os.path.join(SCRIPT_DIR, SCRIPT_FILENAME)

async def get_transcripts(yt_url:str):
    video_id = yt_url.split("watch?v=")[-1].split("&")[0]

    transctips = ytt_api.fetch(video_id, languages=['en', 'zh-Hant', 'zh-Hans'])

    return " ".join([snippet.text for snippet in transctips])

async def get_write_proposal_py(transcription:str, series:str, start_index:int|str, ollama_model:str) -> str:
    start_index = int(start_index)
    with open("inputs/System_Prompt_Proposal_Batch.txt", "r") as f:
        system_prompt = f.read()
    
    contents=f"""
        Make multiple proposals to cover the whole script. Put them into one single python script to save them into "inputs/proposals/{series}_{start_index}.json", "inputs/proposals/{series}_{start_index+1}.json" and so on. Print the base filenames at the end without printing extension ".json". Do not reply anything other than the python script.
        Script:
        {transcription}
        """
    
    async for r in gen_response(contents, [], ollama_model, system_prompt, stream=False):
        response:str = r
    _, _, response = response.rpartition("</think>")
    _, _, response = response.rpartition("```python")
    response, _, _ = response.partition("```")

    # Write the content to the file
    with open(SCRIPT_FULL_PATH, "w") as f:
        f.write(response)
    return f"Successfully wrote script content to {SCRIPT_FULL_PATH}.\n"

async def write_proposals_and_make_topics_file(output_topics_path: str):
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
    )
    yield "Script executed."

    # Prepare output to append
    output_to_append = f"\n--- Output from {SCRIPT_FULL_PATH} ---\n"
    if result.stdout:
        output_to_append += f"--- STDOUT ---\n{result.stdout}\n"
        # Append output to the specified file
        with open(output_topics_path, "a") as f:
            f.write("\n" + result.stdout)
    if result.stderr:
        # Note: Some tools write warnings/info to stderr even on success
        output_to_append += f"--- STDERR ---\n{result.stderr}\n"
    output_to_append += f"--- End Output ---\n"
    yield output_to_append

async def split_line(line:str, proposal_dir:list[str] = ["inputs/proposals", "inputs/proposals/finished"]):
    yt_url, series = line.split()
    
    topic_indices = []
    for p_dir in proposal_dir:
        topic_indices += [topic.removeprefix(f"{series}_").removesuffix(".json") for topic in os.listdir(p_dir) if topic.startswith(series)]
    topic_indices = [int(index) for index in topic_indices if index.isdigit()]
    
    return yt_url, series, max(topic_indices, default=1)

async def transcribe_and_make_proposals(yt_urls_and_series:str, output_topics_path:str, ollama_model:str):
    messages = "Start Generating Proposals... This may take a few minutes...\n"
    yield messages
    for line in yt_urls_and_series.split("\n"):
        if not line.strip() or line.startswith("#"):
            continue
        yt_url, series, start_index = await split_line(line)

        video_transcription = await get_transcripts(yt_url)
        messages += f"Successfully get transcription from {yt_url}.\n"
        yield messages

        messages += await get_write_proposal_py(video_transcription, series, start_index, ollama_model)
        yield messages

        async for msg in write_proposals_and_make_topics_file(output_topics_path):
            messages += msg
            yield messages

    yield f"Successfully appended all topics to '{output_topics_path}'. Refresh the page to see changes.\n"
