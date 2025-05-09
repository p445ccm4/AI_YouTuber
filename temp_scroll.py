import moviepy as mp
import random

def concat_with_motion_blur(clips:list[mp.VideoClip], transition_duration=0.3):
    """
    Concat a list of video clips with motion blur sliding transition.
    
    Args:
        clips (list[mp.VideoClip]): List of video clips to apply the transition to.
        transition_duration (float): Duration of the transition in seconds.
        
    Returns:
        mp.VideoClip: Video clip with motion blur transition applied.
    """
    if len(clips) < 2:
        raise ValueError("At least two clips are required for the transition.")
    output_clips = [clips[0]]
    for clip_B in clips[1:]:
        clip_A = output_clips.pop()

        slide_side = random.choice([("top", "bottom"), ("bottom", "top"), ("left", "right"), ("right", "left")])

        transition_clip = mp.CompositeVideoClip([
                clip_A.subclipped(-transition_duration, None).with_effects([mp.vfx.SlideOut(transition_duration, slide_side[0])]),
                clip_B.subclipped(0, transition_duration).with_effects([mp.vfx.SlideIn(transition_duration, slide_side[1])])
            ]).with_effects([
                mp.vfx.AccelDecel(transition_duration, 3, 1),
                mp.vfx.SuperSample(0.01, 10)
                ])
        
        clips_to_extend = [
            mp.CompositeVideoClip([clip_A.subclipped(0, -transition_duration)]),
            transition_clip,
            mp.CompositeVideoClip([clip_B.subclipped(transition_duration, None)])
        ]
        output_clips.extend(clips_to_extend)
    
    final_clip = mp.concatenate_videoclips(output_clips)
    return final_clip

def make_magifying_start(clip:mp.VideoClip|mp.CompositeVideoClip, duration=0.3, magnification=5.0):
    w, h = clip.size
    clip = clip.with_effects_on_subclip(
        effects=[
            mp.vfx.Resize((lambda t: magnification - t*(magnification-1)/duration), h, w),
            mp.vfx.AccelDecel(duration, 3, 1)
        ],
        start_time=0,
        end_time=duration
    )
    return clip.with_background_color(
        (w, h), (0, 0, 0), opacity=0
        ).with_effects_on_subclip(
            [mp.vfx.SuperSample(0.01, 10)],
            start_time=0,
            end_time=duration
        )

clips = [mp.VideoFileClip(f"outputs/20250506_Relationship_sign_women_like_men_47/{i}_captioned.mp4").with_effects([mp.vfx.SuperSample(0.05, 10)]) for i in range(-1, 3)]

clip = concat_with_motion_blur(clips)

clip = make_magifying_start(clip)

clip.write_videofile("output_fansy.mp4", fps=20)

