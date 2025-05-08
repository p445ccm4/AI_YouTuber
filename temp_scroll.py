import moviepy
import random

def concat_motion_blur(clips:list[moviepy.VideoClip], transition_duration=0.3):
    """
    Create a motion blur transition between two video clips.
    
    Args:
        clips (list[moviepy.VideoClip]): List of video clips to apply the transition to.
        transition_duration (float): Duration of the transition in seconds.
        
    Returns:
        moviepy.VideoClip: Video clip with motion blur transition applied.
    """
    if len(clips) < 2:
        raise ValueError("At least two clips are required for the transition.")
    output_clips = [clips[0]]
    for clip_B in clips[1:]:
        clip_A = output_clips.pop()

        slide_side = random.choice([("top", "bottom"), ("bottom", "top"), ("left", "right"), ("right", "left")])

        transition_clip = moviepy.CompositeVideoClip([
                clip_A.subclipped(-transition_duration, None).with_effects([moviepy.vfx.SlideOut(transition_duration, slide_side[0])]),
                clip_B.subclipped(0, transition_duration).with_effects([moviepy.vfx.SlideIn(transition_duration, slide_side[1])])
            ]).with_effects([moviepy.vfx.AccelDecel(transition_duration, 3, 1)])
        transition_clip.write_videofile("temp.mp4", fps=20)
        transition_clip = moviepy.VideoFileClip("temp.mp4")
        clips_with_effects = [
            clip_A.subclipped(0, -transition_duration),
            transition_clip,
            clip_B.subclipped(transition_duration, None)
        ]

        output_clips.extend(clips_with_effects)
    
    final_clip = moviepy.concatenate_videoclips(output_clips)
    return final_clip.with_effects([moviepy.vfx.SuperSample(0.02, 5)])

clip_A = moviepy.VideoFileClip("output_enlarge.mp4")
clip_B = moviepy.VideoFileClip("output_scroll up.mp4")
w, h = clip_A.size
clip = concat_motion_blur([clip_A, clip_B])
clip.write_videofile("output_transition.mp4", fps=20)

smooth_clip = moviepy.VideoFileClip("output_transition.mp4")
smooth_clip.write_videofile("output_transition_smooth.mp4", fps=20)
