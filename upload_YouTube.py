import argparse
import io
import json
import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import googleapiclient.http
import logging
import webbrowser
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

class YouTubeUploader:
    SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
    CLIENT_SECRETS_FILE_PATH = "inputs/YouTube_Upload_API.json"
    REDIRECT_URL = "http://localhost:8080/"

    def __init__(self, logger=None):
        self.logger = logger or self._setup_logger()
        self._authenticate_youtube()

    def _setup_logger(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        logger = logging.getLogger(__name__)
        return logger
    
    def _authenticate_youtube(self):
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            self.CLIENT_SECRETS_FILE_PATH, self.SCOPES)

        credentials = flow.run_local_server(timeout=10)
        self.youtube = googleapiclient.discovery.build(
            "youtube", "v3", credentials=credentials)

    def upload_video(self, input_video_path, title, description, tags, category_id="24", privacy_status="unlisted"):
        self.logger.info(f"Starting video upload of '{input_video_path}': '{title}'")
        request_body = {
            "snippet": {
                "categoryId": category_id,
                "title": title,
                "description": description,
                "tags": tags if tags is not None else []
            },
            "status": {
                "privacyStatus": privacy_status
            }
        }

        request = self.youtube.videos().insert(
            part="snippet,status",
            body=request_body,
            media_body=googleapiclient.http.MediaFileUpload(input_video_path, chunksize=-1, resumable=True)
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                progress_percentage = int(status.progress() * 100)
                self.logger.info(f"Upload {progress_percentage}%")

        video_id = response['id']
        self.logger.info(f"Video uploaded successfully with ID: {video_id}")

    def upload_from_topic_file(self, topic_file):
        with open(topic_file, 'r') as f:
            topics = [line.split()[0] for line in f.readlines() if line.strip() and not line.strip().startswith("#")]

        successful_topics = []
        failed_topics = []
        for i, topic in enumerate(topics):
            json_file = f"inputs/proposals/{topic}.json"
            topic_file_name = os.path.splitext(os.path.basename(topic_file))[0]
            working_dir = f"outputs/{topic_file_name}_{topic}"

            with open(json_file, 'r') as f:
                data = json.load(f)
                description = data.get('description', "This content is made by me, HiLo World. All right reserved. Contact me if you want to use my content.")
                tags = data.get('tags', None)
                thumbnail = data.get('thumbnail')
                long_title = thumbnail.get('long_title')

            try:
                self.upload_video(
                    input_video_path=f"{working_dir}/final.mp4",
                    description=description,
                    tags=tags,
                    title=long_title
                )
                successful_topics.append(topic)
            except Exception as e:
                self.logger.error(f"Failed to upload video for topic {topic}: {e}")
                failed_topics.append(topic)
            finally:
                yield f"Progress: {i+1}/{len(topics)} videos"

        self.logger.info(f"Successfully uploaded topics:\n{"\n".join(successful_topics)}")
        self.logger.info(f"Failed to upload topics:\n{"\n".join(failed_topics)}")
        yield

def main():
    parser = argparse.ArgumentParser(description="Upload videos to YouTube from a topic file.")
    parser.add_argument("topic_file", help="Path to the topic file.")
    args = parser.parse_args()

    uploader = YouTubeUploader()

    for log_message in uploader.upload_from_topic_file(args.topic_file):
        print(log_message, end='\n')

if __name__ == "__main__":
    main()