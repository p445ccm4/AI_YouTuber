#!/bin/bash
source activate base
conda activate flux

topic_file="inputs/AI_YouTuber/20250211.topics"

Topics=()
Music=()
while IFS= read -r line; do
    topic=$(echo "$line" | awk '{print $1}')
    music=$(echo "$line" | awk '{print $2}')
    Topics+=("$topic")
    Music+=("$music")
done < $topic_file

index=0
for topic in "${Topics[@]}"; do
    echo "Processing $topic"
    json_file="inputs/AI_YouTuber/scripts/${topic}.json"
    topic_file_name=$(basename "$topic_file" .topics)
    working_dir="outputs/HunYuan/${topic_file_name}_${topic}"
    music_path="inputs/AI_YouTuber/music/${Music[$index]}.m4a"
    log_file="${working_dir}/${topic}.log"

    mkdir -p "$working_dir"
    if [ ! -f "$log_file" ]; then
    touch "$log_file"
    fi

    bash AI_YouTuber/run_text2YouTube.sh --json_file "$json_file" --working_dir "$working_dir" --music_path "$music_path" &> "$log_file"
    
    echo "Finished processing $topic"
    ((index++))
done
