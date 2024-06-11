import os.path
import io

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
import requests

# If modifying these scopes, delete the file token.json.
SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/photoslibrary.appendonly"
    ]

def authenticate():
    """
    Authenticates you with the credentials you created
    """
    creds = None
    # Check if token.json exists. The file token.json stores the user's access and refresh tokens, and is created automatically when the authorization flow completes for the first time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no valid credentials, initiate the OAuth 2.0 flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # The credentials.json file must be in the same directory as this script
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=8080)  # This will use as redirect URI http://localhost:8080/ make sure you've enabled it the cloud console
        # Save the credentials for future use
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def filter_images_and_videos(service, page_size=100):
    # Define the query to filter only image files
    query = "mimeType contains 'image/' or mimeType contains 'video/'"
    items = []
    page_token = None

    while True:
        results = service.files().list(
            q=query,
            pageSize=page_size,
            fields="nextPageToken, files(id, name, mimeType, size)",
            pageToken=page_token
        ).execute()

        items.extend(results.get("files", []))
        page_token = results.get("nextPageToken")
        if not page_token:
            break

    return items

def upload_to_photos(session, creds, file_path, file_name, mime_type):
    upload_url = "https://photoslibrary.googleapis.com/v1/uploads"
    headers = {
        "Authorization": "Bearer " + creds.token,
        "Content-Type": "application/octet-stream",
        "X-Goog-Upload-File-Name": os.path.basename(file_path),
        "X-Goog-Upload-Content-Type": mime_type,
        "X-Goog-Upload-Protocol": "raw"
    }
    with open(file_path, 'rb') as file:
        response = session.post(upload_url, headers=headers, data=file)
    upload_token = response.content.decode('utf-8')

    create_url = "https://photoslibrary.googleapis.com/v1/mediaItems:batchCreate"
    headers = {
        "Authorization": "Bearer " + creds.token,
        "Content-Type": "application/json"
    }
    json_body = {
        "newMediaItems": [
            # TODO Include as many NewMediaItems as possible in each call to batchCreate to minimize the total number of calls you have to make. At most you can include 50 items.
            {
                "description": "Uploaded from Google Drive",
                "simpleMediaItem": {
                    "fileName": file_name,
                    "uploadToken": upload_token
                }
            }
        ]
    }
    response = session.post(create_url, headers=headers, json=json_body)
    return response.json()

def main():
  """Shows basic usage of the Drive v3 API.
  Prints the names and ids of the first 10 files the user has access to.
  """
  creds = authenticate()

  try:
    service = build("drive", "v3", credentials=creds)
    session = requests.Session()

    # Call the Drive v3 API
    files = filter_images_and_videos(service)
    if not files:
        print("No files found.")
        return

    print("Total images & videos:", len(files))
    if len(files) > 10000:
        print("Unable to run, total files exceed API limit of 10.000 / day. Contact your developer for making the necessary modifications")
        return
    total_size_bytes = 0
    for file in files:
        size = int(file.get('size', 0))  # Get the file size, default to 0 if not available
        total_size_bytes += size

        # Download the file from Google Drive
        request = service.files().get_media(fileId=file['id'])
        file_name = file['name']
        file_path = os.path.join('/tmp', file_name)
        fh = io.FileIO(file_path, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print(f"Downloading {file_name} {int(status.progress() * 100)}%.")

        # Upload the file to Google Photos
        response = upload_to_photos(session, creds, file_path, file_name, file['mimeType'])
        if response['newMediaItemResults'][0]['status']['message'] == "Success":
            with open("upload_report.txt", 'a') as log_file:
                log_file.write(f"Uploaded {file_name} to Google Photos" + '\n')
        else:
            with open("upload_report.txt", 'a') as log_file:
                log_file.write(f"Error! {file_name} upload failed." + '\n')

        # Delete the file from the temporary directory
        os.remove(file_path)
        print(f"Deleted temporary file: {file_path}")

    # Convert total size to MB and GB
    total_size_mb = total_size_bytes / (1024 * 1024)
    total_size_gb = total_size_bytes / (1024 * 1024 * 1024)
    if total_size_gb > 1:
        print("Total size (GB):", total_size_gb)
    else:
        print("Total size (MB):", total_size_mb)

  except HttpError as error:
    # Handle errors from Drive API.
    print(f"An error occurred: {error}")


if __name__ == "__main__":
  main()