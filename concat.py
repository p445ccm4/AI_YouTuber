import random
import moviepy as mp
import os
import argparse
import logging

def sort_by_startint(a):
    return int(a.split("_")[0])

class VideoConcatenator:
    def __init__(self, working_dir, make_shorts=False, logger=None):
        self.working_dir = working_dir
        self.logger = logger
        size = (720, 1280) if make_shorts else (1280, 720) 
        self.swoosh_transition = mp.ColorClip(size=size, is_mask=True).with_audio(mp.AudioFileClip("inputs/swoosh.mp3").with_volume_scaled(0.3))
        self.swoosh_start = mp.ColorClip(size=size, is_mask=True).with_audio(mp.AudioFileClip("inputs/swoosh_1s.mp3").with_volume_scaled(0.5))


    def concat_with_motion_blur(self, clips:list[mp.VideoClip], transition_duration=0.3):
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
        
        output_clips = [mp.CompositeVideoClip([clips[0]])]
        for clip_B in clips[1:]:
            clip_A = output_clips.pop()

            slide_side = random.choice([("top", "bottom"), ("bottom", "top"), ("left", "right"), ("right", "left")])

            transition_clip = mp.CompositeVideoClip([
                self.swoosh_transition.with_duration(transition_duration),
                clip_A.subclipped(-transition_duration, None).with_effects([mp.vfx.SlideOut(transition_duration, slide_side[0])]),
                clip_B.to_ImageClip(t=0.01, duration=transition_duration).with_effects([mp.vfx.SlideIn(transition_duration, slide_side[1])]),
            ]).with_effects([
                mp.vfx.AccelDecel(transition_duration, 3, 1),
                mp.vfx.SuperSample(0.01, 10)
            ])
            
            clips_to_extend = [
                clip_A.subclipped(0, -transition_duration),
                transition_clip,
                mp.CompositeVideoClip([clip_B])
            ]
            output_clips.extend(clips_to_extend)
        
        final_clip = mp.concatenate_videoclips(output_clips)
        return final_clip

    def make_magifying_start(self, clip:mp.VideoClip|mp.CompositeVideoClip, duration=0.3, magnification=5.0):
        w, h = clip.size
        clip = mp.CompositeVideoClip([
            self.swoosh_start.with_duration(1),
            clip.with_effects_on_subclip(
                effects=[
                    mp.vfx.Resize((lambda t: magnification - t*(magnification-1)/duration), h, w),
                    mp.vfx.AccelDecel(duration, 3, 1),
                    mp.vfx.Crop(x_center=w/2, y_center=h/2, width=w, height=h)
                ],
                start_time=0,
                end_time=duration
            ),
        ])
        return clip.with_background_color(
            (w, h), (0, 0, 0), opacity=0
        )

    def concatenate_videos(self):
        vid_list = [f for f in os.listdir(self.working_dir) if f.endswith("_captioned.mp4")]
        vid_list = sorted(vid_list, key=sort_by_startint)
        clips = [mp.VideoFileClip(os.path.join(self.working_dir, f)) for f in vid_list]

        self.logger.info(f"clips: {vid_list}")

        # Concatenate all clips
        concat_clip = self.concat_with_motion_blur(clips)
        concat_clip = self.make_magifying_start(concat_clip)
        concat_clip = concat_clip.with_effects([
            mp.vfx.SuperSample(0.01, 10)
        ])
        concat_clip.write_videofile(os.path.join(self.working_dir, "concat.mp4"), ffmpeg_params=["-hide_banner", "-loglevel", "error"])

        self.logger.info("Video concatenation complete.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(description="Concatenate video clips in a directory.")
    parser.add_argument("--working_dir", "-o", help="The directory containing the video clips.")
    args = parser.parse_args()

    concatenator = VideoConcatenator(args.working_dir, logger)
    concatenator.concatenate_videos()
