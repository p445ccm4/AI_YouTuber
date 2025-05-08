import random
import moviepy as mp
import os
import argparse
import logging

class VideoConcatenator:
    def __init__(self, working_dir, logger=None):
        self.working_dir = working_dir
        self.logger = logger

    def sort_by_startint(self, a):
        return int(a.split("_")[0])

    def concat_with_motion_blur(self, clips:list[mp.VideoClip], transition_duration=0.3):
        """
        Create a motion blur transition between two video clips.
        
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
                ]).with_effects([mp.vfx.AccelDecel(transition_duration, 3, 1)])
            transition_clip.write_videofile("temp.mp4", fps=20)
            transition_clip = mp.VideoFileClip("temp.mp4")
            clips_with_effects = [
                clip_A.subclipped(0, -transition_duration),
                transition_clip,
                clip_B.subclipped(transition_duration, None)
            ]

            output_clips.extend(clips_with_effects)
        
        final_clip = mp.concatenate_videoclips(output_clips)
        return final_clip.with_effects([mp.vfx.SuperSample(0.02, 5)])

    def concatenate_videos(self):
        vid_list = [f for f in os.listdir(self.working_dir) if f.endswith("_captioned.mp4")]
        vid_list = sorted(vid_list, key=self.sort_by_startint)
        clips = [mp.VideoFileClip(os.path.join(self.working_dir, f)) for f in vid_list]

        self.logger.info(f"clips: {vid_list}")

        # Concatenate all clips
        concat_clip = self.concat_with_motion_blur(clips)
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
