import os
import google_auth_oauthlib
import googleapiclient.discovery
import googleapiclient.errors
import googleapiclient.http
import logging
import argparse

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_FILE = 'token.json'

def authenticate_youtube(client_secrets_file_path):
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrets_file_path, SCOPES)

    credentials = flow.run_local_server()
    youtube = googleapiclient.discovery.build(
        "youtube", "v3", credentials=credentials)
    return youtube

class YouTubeUploader:
    def __init__(self, youtube=None, client_secrets_file_path="inputs/YouTube_Upload_API.json", logger=None):
        self.logger = logger
        self.youtube = youtube or authenticate_youtube(client_secrets_file_path)

    def upload_video(self, input_video_path, title, description="Please SUBSRIBE me to help reach 1000 subs!", tags=None, category_id="24", privacy_status="unlisted"):
        self.logger.info(f"Starting video upload: '{title}' from '{input_video_path}'")
        request_body = {
            "snippet": {
                "categoryId": category_id,
                "title": title,
                "description": description,
                "tags": tags if tags is not None else []
            },
            "status":{
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
                progress_percentage = int(status.progress()*100)
                self.logger.info(f"Upload {progress_percentage}%")

        video_id = response['id']
        self.logger.info(f"Video uploaded successfully with ID: {video_id}")


def main():
    parser = argparse.ArgumentParser(description="Upload a video to YouTube.")
    parser.add_argument("video_path", help="Path to the video file to upload.")
    parser.add_argument("video_title", help="Title of the video.")

    args = parser.parse_args()

    # Configure basic logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    uploader = YouTubeUploader(logger=logger)
    uploader.upload_video(args.video_path, args.video_title)

if __name__ == "__main__":
    main()