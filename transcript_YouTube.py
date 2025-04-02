from youtube_transcript_api import YouTubeTranscriptApi
import llm
import json

ytt_api = YouTubeTranscriptApi()

def get_transcripts(yt_url:str):
    video_id = yt_url.split("watch?v=")[-1].split("&")[0]

    transctips = ytt_api.fetch(video_id, languages=['en', 'zh-Hant', 'zh-Hans'])

    return " ".join([snippet.text for snippet in transctips]), video_id

def make_proposals(yt_urls:str, series:str, topics_path:str):
    with open("inputs/System_Prompt_Proposal.txt", "r") as f:
        system_prompt = f.read()
    for yt_url in yt_urls.split("\n"):
        if not yt_url.strip() or yt_url.startswith("#"):
            continue

        if " " in yt_url:
            yt_url, n_shorts = yt_url.split(" ", 1)
        else:
            n_shorts = 1

        video_transcription, video_id = get_transcripts(yt_url)

        return video_transcription
