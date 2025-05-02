import moviepy as mp
import numpy as np

def accelerating_crossfade(video_path1, video_path2, crossfade_duration):
    """
    Applies an accelerating crossfade effect between two videos.

    Args:
        video_path1: Path to the first video file.
        video_path2: Path to the second video file.
        crossfade_duration: Duration of the crossfade in seconds.
        acceleration_factor: Factor by which to accelerate the crossfade speed.

    Returns:
        A CompositeVideoClip with the crossfade effect.
    """

    clip1 = mp.VideoFileClip(video_path1)
    clip2 = mp.VideoFileClip(video_path2)

    # Create crossfade with accelerating speed
    crossfade = mp.CompositeVideoClip([
        clip1.subclipped(-crossfade_duration).with_effects([mp.vfx.CrossFadeOut(crossfade_duration)]),
        clip2.subclipped(0, crossfade_duration).with_effects([mp.vfx.CrossFadeIn(crossfade_duration)])
        ])
    crossfade = crossfade.with_effects([mp.vfx.AccelDecel(None, 20, 1)])
    
    # return crossfade

    clip1 = clip1.subclipped(0, -crossfade_duration)
    clip2 = clip2.subclipped(crossfade_duration, clip2.duration)
    final_clip = mp.concatenate_videoclips([
        clip1,
        crossfade,
        clip2
    ])

    return final_clip

# Example usage:
video_file1 = "outputs/20250411_Motivation_13/0_captioned.mp4"
video_file2 = "outputs/20250411_Motivation_13/1_captioned.mp4"
fade_time = 0.5

final_video = accelerating_crossfade(video_file1, video_file2, fade_time)
final_video.write_videofile("accelerated_crossfade_video.mp4", fps=20)