#!/bin/bash

source activate base
conda activate flux

json_file="inputs/AI_YouTuber/scripts/100usd.json"
working_dir="outputs/HunYuan/20250211_100usd"
music_path="inputs/AI_YouTuber/music/News.m4a"

mkdir -p "$working_dir"
failed_indices=()
jq -c '.[]' $json_file | while read element; do
    # Check if the element starts with '{', if not, add it
    if [[ ! "$element" =~ ^\{.* ]] ; then
        element="{${element}"
    fi
    index=$(jq -r '.index' <<< "$element")
    caption=$(jq -r '.caption' <<< "$element")
    prompt=$(jq -r '.prompt' <<< "$element")
    voiceover=$(jq -r '.voiceover' <<< "$element")

    echo "Index: $index"
    echo "Caption: $caption"
    echo "Prompt: $prompt"
    echo "Voiceover: $voiceover"

    python AI_YouTuber/gen_audio.py -i $index -c "$voiceover" -o $working_dir
    python AI_YouTuber/gen_video.py -i $index -e "$prompt" -o $working_dir
    python AI_YouTuber/interpolate.py --input_video_path $working_dir/$index.mp4 --output_video_path $working_dir/${index}_interpolated.mp4
    python AI_YouTuber/audio_caption.py --audio_path $working_dir/$index.mp3 --caption "$caption" --input_video_path $working_dir/${index}_interpolated.mp4 --output_video_path $working_dir/${index}_captioned.mp4
    
    if [ $? -ne 0 ]; then
        echo "Error encountered with index=$index. Skipping..."
        failed_indices+=($index)
    else
        echo "Successfully processed iteration with index=$index"
    fi
done

trap 'echo "Failed iterations so far: ${failed_indices[@]}"; exit' INT TERM

if [ ${#failed_indices[@]} -eq 0 ]; then
    echo "All iterations completed successfully!"
    python AI_YouTuber/concat.py -o $working_dir
    python AI_YouTuber/bg_music.py --input_video_path $working_dir/concat.mp4 --music_path "$music_path" --output_video_path $working_dir.mp4
    echo "concat.py completed successfully!"
else
    echo "Some iterations failed. concat.py will not be run."
    echo "Failed iterations: ${failed_indices[@]}"
fi