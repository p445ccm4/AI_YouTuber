import math
import os
from moviepy.editor import *
import cv2

input_path = "inputs/美國大選進入衝刺階段, 比特幣暴升7%, 站上7.3萬美元上方, 期權定價顯示明日波動幅度達8%.txt"
data_dir_path = "outputs"
output_path = os.path.join(data_dir_path, "FINAL.mp4")
os.makedirs(os.path.join(data_dir_path, "temp"), exist_ok=True)
with open(input_path) as f:
    texts = f.readlines()[0]
    texts = texts.removesuffix("\n").split(", ")
    texts = [", ".join(texts[i:i+3]) for i in range(len(texts)-2)]

clips = []
for i, text in enumerate(texts):
    # Usage
    video_path = os.path.join(data_dir_path, f"{i}_{text}.mp4")
    audio_path = os.path.join(data_dir_path, f"{i}_{text}.mp3")
    image_path = os.path.join(data_dir_path, f"{i}_{text}.png")

    # Load files
    video_clip = VideoFileClip(video_path)
    w, h = video_clip.size
    t = math.ceil(video_clip.duration)
    image = cv2.imread(image_path)
    img_h, img_w, _ = image.shape
    scale = max(h/img_h, (w+t*10)/img_w)
    image = cv2.resize(image, None, fx=scale, fy=scale)
    img_h, img_w, _ = image.shape
    cv2.imwrite(os.path.join(data_dir_path, "temp", f"{i}_{text}.png"), image[img_h//2-h//2:img_h//2+h//2, img_w//2-w//2-t*5:img_w//2+w//2+t*5])
    image_path = os.path.join(data_dir_path, "temp", f"{i}_{text}.png")

    audio_clip = AudioFileClip(audio_path)
    image_clip = ImageClip(image_path)
    text_clip = TextClip(text, fontsize=70, color='white').set_duration(audio_clip.duration).set_position(('center', 'bottom'))

    audio_video_diff = audio_clip.duration - video_clip.duration
    # If the final audio is longer than the video, append image after video to match the audio duration
    if audio_video_diff > 0:
        image_clip = image_clip.set_duration(audio_video_diff).set_start(video_clip.duration).set_position(lambda x: (x * 10 - t*10, 'center'))
        # Combine everything
        clip = CompositeVideoClip([video_clip, image_clip, text_clip])

    # If the final audio is shorter than the video, loop it to match the video duration
    else:
        video_clip = video_clip.subclip(0, audio_clip.duration)
        # Combine everything
        clip = CompositeVideoClip([video_clip, text_clip])

    # Set the audio of the video clip
    clip = clip.set_audio(audio_clip)
    
    clips.append(clip)

# Write the result to a file
final_clip = concatenate_videoclips(clips, method="compose")
final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
