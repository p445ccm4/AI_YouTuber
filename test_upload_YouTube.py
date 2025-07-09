import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

class YouTubeAuthenticator:
    """
    A class to handle YouTube API authentication for Gradio.
    """
    def __init__(self, client_secrets_file_path, scopes):
        self.CLIENT_SECRETS_FILE_PATH = client_secrets_file_path
        self.SCOPES = scopes
        self.youtube = None
        self.credentials = None # Store credentials for potential reuse

    def _authenticate_youtube_for_gradio(self):
        """
        Authenticates with YouTube API using a flow suitable for Gradio shared links.
        This method will print an authorization URL and prompt the user to paste
        the authorization code back.

        Returns:
            google.oauth2.credentials.Credentials: The authenticated credentials,
                                                    or None if authentication fails.
        """
        # Disable OAUTHlib's HTTPS requirement for local testing/development
        # Remove this in production if you are using HTTPS.
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        # Check if credentials already exist and are valid
        if self.credentials and self.credentials.valid:
            if self.credentials.expired and self.credentials.refresh_token:
                print("Refreshing existing credentials...")
                self.credentials.refresh(Request())
            else:
                print("Using existing valid credentials.")
                self.youtube = googleapiclient.discovery.build(
                    "youtube", "v3", credentials=self.credentials)
                return self.credentials

        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            self.CLIENT_SECRETS_FILE_PATH, self.SCOPES)

        # Set the redirect URI for out-of-band (OOB) flow
        # This tells Google to display the authorization code in the browser
        # after the user grants permission.
        flow.redirect_uri = "urn:ietf:wg:oauth:2.0:oob"

        print("\n--- Google OAuth Authentication ---")
        print("Please visit this URL in your web browser to authorize access:")
        # Generate the authorization URL
        auth_url, _ = flow.authorization_url(prompt='consent')
        print(auth_url)
        print("\nAfter authorizing, copy the 'authorization code' from the page")
        print("and paste it here, then press Enter:")

        # This part needs to be handled by Gradio's input component
        # For a direct Python script, you'd use input()
        # For Gradio, you'd pass this URL to a Gradio Text component,
        # and then have another Gradio Textbox for the user to paste the code.
        # This function will need to be split into two parts for Gradio:
        # 1. Generate URL and display it.
        # 2. Take user-provided code and complete the flow.

        # For demonstration purposes, this part simulates getting input:
        # In a real Gradio app, this 'input()' would be replaced by a Gradio
        # event listener that gets the code from a UI component.
        try:
            authorization_response = input("Enter the authorization code: ")
            flow.fetch_token(code=authorization_response)
        except Exception as e:
            print(f"Error fetching token: {e}")
            return None

        self.credentials = flow.credentials
        self.youtube = googleapiclient.discovery.build(
            "youtube", "v3", credentials=self.credentials)
        print("Authentication successful!")
        return self.credentials

# Example Usage (for testing purposes, not directly runnable in Gradio as-is)
if __name__ == "__main__":
    # Replace with your actual client secrets file and desired scopes
    CLIENT_SECRETS_FILE = "inputs/YouTube_Upload_API.json"
    SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"] # Example scope

    # # Create a dummy client_secret.json for testing if it doesn't exist
    # if not os.path.exists(CLIENT_SECRETS_FILE):
    #     print(f"Creating a dummy {CLIENT_SECRETS_FILE}. Please replace with your actual file.")
    #     dummy_content = {
    #         "web": {
    #             "client_id": "YOUR_CLIENT_ID",
    #             "project_id": "YOUR_PROJECT_ID",
    #             "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    #             "token_uri": "https://oauth2.googleapis.com/token",
    #             "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    #             "client_secret": "YOUR_CLIENT_SECRET",
    #             "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost:8080"]
    #         }
    #     }
    #     import json
    #     with open(CLIENT_SECRETS_FILE, "w") as f:
    #         json.dump(dummy_content, f, indent=4)

    authenticator = YouTubeAuthenticator(CLIENT_SECRETS_FILE, SCOPES)
    credentials = authenticator._authenticate_youtube_for_gradio()

    if credentials:
        print("\nCredentials obtained successfully!")
        # You can now use authenticator.youtube to make API calls
        # For example:
        # request = authenticator.youtube.channels().list(
        #     part="snippet,contentDetails,statistics",
        #     mine=True
        # )
        # response = request.execute()
        # print(response)
    else:
        print("\nAuthentication failed.")
