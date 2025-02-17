import os
import text2YTShorts_single
import logging

topic_file = "inputs/AI_YouTuber/20250213.topics"
with open(topic_file, 'r') as f:
    lines = f.readlines()

for line in lines:
    line = line.strip()
    if line.startswith("#") or not line:
        continue
    line = line.split()
    topic = line[0]
    music = line[1]
    indices_to_process = [int(i) for i in line[2:]] if len(line) > 2 else None # None if no indices provided

    print(f"Processing {topic}")
    json_file = f"inputs/AI_YouTuber/scripts/{topic}.json"
    topic_file_name = os.path.splitext(os.path.basename(topic_file))[0]
    working_dir = f"outputs/HunYuan/{topic_file_name}_{topic}"
    music_path = f"inputs/AI_YouTuber/music/{music}.m4a"
    log_file = os.path.join(working_dir, f"{topic}.log")

    os.makedirs(working_dir, exist_ok=True)
    if not os.path.exists(log_file):
        open(log_file, 'a').close()
    logging.basicConfig(filename=log_file, level=logging.ERROR, 
                        format='%(asctime)s - %(levelname)s - %(message)s')

    print(f"Starting processing for {topic}")
    try:
        shorts_maker = text2YTShorts_single.YTShortsMaker(
            json_file,
            working_dir, 
            music_path, 
            indices_to_process,
            logger=logging.getLogger(log_file)
        )
        shorts_maker.run()
        print(f"Finished processing {topic} successfully")
    except Exception as e:
        print(f"Error processing {topic}: {e}")

