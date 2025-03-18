import os
import json
import argparse

def check_videos(folder_path, topic):
    final_video = os.path.join(folder_path, f"final.mp4")
    music_file = os.path.join(folder_path, f"music.wav")

    if os.path.exists(final_video):
        return "finished", topic
    
    failed_indices = []
    if not os.path.exists(music_file):
        failed_indices.append("99")

    for i in range(-1, 26):
        captioned_file = os.path.join(folder_path, f"{i}_captioned.mp4")
        if not os.path.exists(captioned_file):
            failed_indices.append(str(i))

    if failed_indices:
        return "partially done", topic + ' ' + ' '.join(failed_indices)
    return "not started", topic


def print_status(input_topics, outputs_path = "outputs", proposal_path = "inputs/proposals"):
    with open(input_topics, 'r') as f:
        topics = f.readlines()

    prefix = os.path.basename(input_topics).split(".")[0]
    topics = [topic.split()[0].strip() for topic in topics if topic.strip() and not topic.strip().startswith("#")]
    status_all = {}
    for topic in topics:
        folder_name = f"{prefix}_{topic}"
        folder_path = os.path.join(outputs_path, folder_name)
        if os.path.isdir(folder_path):
            status, line = check_videos(folder_path, topic)
            if status == "finished":
                with open(f"{proposal_path}/{folder_name.split("_", maxsplit=1)[-1]}.json", 'r') as f:
                    title = json.load(f).get("thumbnail", {}).get("long_title")
                line += f" \"{title}\""
            status_all[status] = [*status_all.get(status, []), line]
        else:
            status_all["not started"] = [*status_all.get("not started", []), folder_name]

    output_string = ""
    for status, lines in status_all.items():
        output_string += f"\n# {status} jobs:\n\n"
        output_string += "\n".join(lines) + "\n"
    return output_string

if __name__ == "__main__": 
    parser = argparse.ArgumentParser()
    parser.add_argument("input_topics")
    args = parser.parse_args()

    print(print_status(args.input_topics))