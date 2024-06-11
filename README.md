# Google Drive to Google Photos Uploader

The purpose of this script is to upload all images & videos that exist on a user's Google Drive to their Google Photos account, using the corresponding APIs. If there are more than 10,000 files to be uploaded, the script will not run due to API restrictions listed [here](https://developers.google.com/photos/library/guides/api-limits-quotas).

This script does not delete the uploaded files from the user's Google Drive account, so files will exist both on Google Drive and Google Photos. If such functionality is required, further modifications are needed.

This script is tested on Mac, modifications may be needed to work on Windows.

## Prerequisites

- Python 3.10.7 or greater
- The `pip` package management tool

## Instructions

1. **Enable Google Drive & Google Photos APIs:**
   - Go to the [Cloud Console](https://console.cloud.google.com/apis/library).
   - Enable the Google Drive API and Google Photos Library API.
   - Set the redirect URI to `http://localhost:8080/` (or use the port specified in the script).
   - Download the Google Drive credentials JSON file, rename it to `credentials.json`, and save it in the same directory as this Python script (`photos_uploader.py`).

2. **Create and activate a virtual environment:**
   ```bash
   pip3 install virtualenv
   python3 -m venv myvenv
   source myvenv/bin/activate
   ```

3. **Install the project's requirements:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the project:**
   ```bash
   python photos_uploader.py
   ```

5. **Authenticate your app:**
   - Click "Allow" in the new browser window to authenticate your app with Google.

6. **Review upload status:**
   - Check `upload_report.txt` to review the upload status of each file. You can find files that failed to upload to Photos (if any) by searching for the keyword `Error!` and then upload them manually.

7. **Cleanup:**
    - For security reasons, permanent deletion of `credentials.json` and `token.json` after execution of the script is recommended.

## Optimizations Roadmap

1. Upload multiple files with each call to `batchCreate` to minimize the total number of API calls. At most, you can include 50 items.
2. Enable resumable uploads for large files and bandwidth savings. [More details](https://developers.google.com/photos/library/guides/resumable-uploads)

## API Documentation

- [Getting started with Google Drive API](https://developers.google.com/drive/api/quickstart/python).
- [Uploading media to Google Photos](https://developers.google.com/photos/library/guides/upload-media).