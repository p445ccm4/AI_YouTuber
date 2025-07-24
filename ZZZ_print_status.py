import os
import json
import argparse

async def check_one_topic(folder_path, topic, indices):
    
    final_video_path = os.path.join(folder_path, f"final.mp4")
    concat_video_path = os.path.join(folder_path, f"concat.mp4")
    music_path = os.path.join(folder_path, f"music.wav")
    thumbnail_path = os.path.join(folder_path, f"-1_captioned.png")

    if not os.path.exists(folder_path):
        return "not started", topic

    if os.path.exists(final_video_path) and os.path.exists(thumbnail_path):
        return "finished", topic
    
    failed_indices = []
    if not os.path.exists(music_path):
        failed_indices.append("-3")
    if not os.path.exists(concat_video_path):
        failed_indices.append("-2")
    if not os.path.exists(thumbnail_path):
        failed_indices.append("-1")
    for i in indices:
        captioned_file = os.path.join(folder_path, f"{i}_captioned.mp4")
        if not os.path.exists(captioned_file):
            failed_indices.append(str(i))

    return "partially done", topic + ' ' + ' '.join(failed_indices)

async def check_topics(topics: list[str], prefix: str, outputs_path: str = "outputs", proposal_path: str = "inputs/proposals"):
    status_dict = {"not started":[], "partially done":[], "finished":[]}
    for topic in topics:
        folder_name = f"{prefix}_{topic}"
        folder_path = os.path.join(outputs_path, folder_name)
        with open(f"{proposal_path}/{folder_name.split("_", maxsplit=1)[-1]}.json", 'r') as f:
            data = json.load(f)
            title = data.get("thumbnail", {}).get("long_title")
            indices = [int(caption.get("index")) for caption in data.get("script")]

        status, line = await check_one_topic(folder_path, topic, indices)
        if status == "finished":
            line += f" \"{title}\""
        status_dict[status].append(line)

    return status_dict

async def print_status(input_topics):
    with open(input_topics, 'r') as f:
        topics = f.readlines()

    prefix = os.path.basename(input_topics).split(".")[0]
    
    topics_shorts, topics_longs = [], []
    for topic in topics:
        topic = topic.strip()
        if topic and not topic.endswith(":"):
            while topic.startswith("# "):
                topic = topic.removeprefix("# ")
            topic = topic.split()[0].strip() 
            if "shorts" in topic:
                topics_shorts.append(topic)
            else:
                topics_longs.append(topic)

    status_shorts = await check_topics(topics_shorts, prefix)
    status_longs = await check_topics(topics_longs, prefix)

    output_string = "# Shorts:\n"
    for status, lines in status_shorts.items():
        if lines:
            output_string += f"\n# {status} jobs:\n\n"
            output_string += "\n".join(lines) + "\n"

    output_string += "\n# Longs:\n"
    for status, lines in status_longs.items():
        if lines:
            output_string += f"\n# {status} jobs:\n\n"
            output_string += "\n".join(lines) + "\n"

    return output_string

if __name__ == "__main__": 
    parser = argparse.ArgumentParser()
    parser.add_argument("input_topics")
    args = parser.parse_args()

    import asyncio
    result = asyncio.run(print_status(args.input_topics))
    print(result)