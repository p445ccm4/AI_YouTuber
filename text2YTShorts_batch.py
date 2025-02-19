import os
import text2YTShorts_single_moreAI
import logging
import argparse

parser = argparse.ArgumentParser(description="Process topics from a file.")
parser.add_argument("topic_file", help="Path to the topic file.")
args = parser.parse_args()
topic_file = args.topic_file
with open(topic_file, 'r') as f:
    lines = f.readlines()

for line in lines:
    line = line.strip()
    if line.startswith("#") or not line:
        continue
    line = line.split()
    topic = line[0]
    music = line[1] if len(line) > 1 and line[1] != "None" else None
    indices_to_process = [int(i) for i in line[2:]] if len(line) > 2 else None # None if no indices provided

    print(f"Processing {topic}")
    json_file = f"inputs/proposals/{topic}.json"
    topic_file_name = os.path.splitext(os.path.basename(topic_file))[0]
    working_dir = f"outputs/{topic_file_name}_{topic}"
    music_path = f"inputs/music/{music}.m4a" if music else None
    log_file = os.path.join(working_dir, f"{topic}.log")

    os.makedirs(working_dir, exist_ok=True)
    open(log_file, 'a').close()
    #BUG: cannot log to file
    logging.basicConfig(filename=log_file, level=logging.INFO, 
                        format='%(asctime)s - %(levelname)s - %(message)s')

    print(f"Starting processing for {topic}")
    try:
        shorts_maker = text2YTShorts_single_moreAI.YTShortsMaker(
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

