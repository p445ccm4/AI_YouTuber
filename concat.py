import moviepy as mp
import os
import argparse
import logging

class VideoConcatenator:
    def __init__(self, working_dir, logger=None):
        self.working_dir = working_dir
        self.logger = logger if logger else logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def sort_by_startint(self, a):
        return int(a.split("_")[0])

    def concatenate_videos(self):
        vid_list = [f for f in os.listdir(self.working_dir) if f.endswith("_captioned.mp4")]
        vid_list = sorted(vid_list, key=self.sort_by_startint)
        clips = [mp.VideoFileClip(os.path.join(self.working_dir, f)) for f in vid_list]

        self.logger.info(f"clips: {vid_list}")

        # Concatenate all clips
        concat_clip = mp.concatenate_videoclips(clips)
        concat_clip.write_videofile(os.path.join(self.working_dir, "concat.mp4"), logger=None)

        self.logger.info("Video concatenation complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Concatenate video clips in a directory.")
    parser.add_argument("--working_dir", "-o", help="The directory containing the video clips.")
    args = parser.parse_args()

    concatenator = VideoConcatenator(args.working_dir)
    concatenator.concatenate_videos()
