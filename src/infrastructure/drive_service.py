"""
Infrastructure Layer: Google Drive Service

Handles uploading images to Google Drive.
Supports both Service Account (cloud) and OAuth 2.0 (local dev).
"""

import os
import io
import json
from typing import Optional
from dataclasses import dataclass
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

import logging
logger = logging.getLogger(__name__)


@dataclass
class UploadResult:
    """Result of uploading to Google Drive."""
    success: bool
    file_id: Optional[str] = None
    file_url: Optional[str] = None
    error_message: Optional[str] = None


class GoogleDriveService:
    """
    Service for uploading images to Google Drive.

    Uses OAuth 2.0 for authentication (user's own Drive storage).
    """

    SCOPES = ['https://www.googleapis.com/auth/drive.file']

    def __init__(self, credentials_file: str, folder_id: str, token_file: str = None):
        """
        Initialize Google Drive service.

        Args:
            credentials_file: Path to OAuth credentials JSON file
            folder_id: Google Drive folder ID to upload to
            token_file: Path to store/load token (default: token.json in same dir)
        """
        self.credentials_file = credentials_file
        self.folder_id = folder_id
        self.token_file = token_file or os.path.join(
            os.path.dirname(credentials_file), 'token.json'
        )
        self.service = None
        self._initialize_service()

    def _is_service_account(self) -> bool:
        """Check if the credentials file is a service account key."""
        try:
            with open(self.credentials_file, 'r') as f:
                data = json.load(f)
            return data.get('type') == 'service_account'
        except Exception:
            return False

    def _initialize_service(self):
        """Initialize the Drive service. Auto-detects credential type."""
        if self._is_service_account():
            self._init_with_service_account()
        else:
            self._init_with_oauth()

    def _init_with_service_account(self):
        """Initialize using Service Account credentials (for cloud deployment)."""
        creds = service_account.Credentials.from_service_account_file(
            self.credentials_file, scopes=self.SCOPES
        )
        self.service = build('drive', 'v3', credentials=creds)
        logger.info("✅ [Drive] Service initialized with Service Account")

    def _init_with_oauth(self):
        """Initialize using OAuth 2.0 credentials (for local development)."""
        creds = None

        # Load existing token if available
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)

        # If no valid credentials, need to authorize
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                # Refresh expired token
                creds.refresh(Request())
            else:
                # Run OAuth flow (manual authorization for WSL/headless environments)
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES
                )
                # Generate auth URL with loopback redirect
                flow.redirect_uri = 'http://localhost:8080/'
                auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')

                logger.info("=" * 60)
                logger.info("🔐 需要授權 Google Drive 存取權限")
                logger.info("=" * 60)
                logger.info(f"\n1. 請在瀏覽器開啟此網址：\n\n{auth_url}\n")
                logger.info("2. 授權後，瀏覽器會顯示「無法連線」錯誤")
                logger.info("3. 從網址列複製 code= 後面的內容（到 & 之前）")
                logger.info("   例如: http://localhost:8080/?code=4/0XXXXX&scope=...")
                logger.info("   只需要複製 4/0XXXXX 這部分")
                logger.info("=" * 60)
                code = input("\n請貼上授權碼: ").strip()
                flow.fetch_token(code=code)
                creds = flow.credentials

            # Save token for future use
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
            logger.info(f"✅ [Drive] Token saved to {self.token_file}")

        self.service = build('drive', 'v3', credentials=creds)
        logger.info("✅ [Drive] Service initialized with OAuth")

    def upload_image(
        self,
        image_data: bytes,
        filename: str,
        mime_type: str = "image/jpeg"
    ) -> UploadResult:
        """
        Upload image to Google Drive.

        Args:
            image_data: Image binary data
            filename: Name for the uploaded file
            mime_type: MIME type of the image

        Returns:
            UploadResult with file ID and public URL
        """
        try:
            # Create file metadata
            file_metadata = {
                'name': filename,
                'parents': [self.folder_id]
            }

            # Create media upload
            media = MediaIoBaseUpload(
                io.BytesIO(image_data),
                mimetype=mime_type,
                resumable=True
            )

            # Upload file
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink'
            ).execute()

            file_id = file.get('id')

            # Make file publicly accessible
            self.service.permissions().create(
                fileId=file_id,
                body={'type': 'anyone', 'role': 'reader'}
            ).execute()

            # Get the public view link
            file_url = f"https://drive.google.com/file/d/{file_id}/view"

            logger.info(f"📤 [Drive] Uploaded: {filename} -> {file_url}")

            return UploadResult(
                success=True,
                file_id=file_id,
                file_url=file_url
            )

        except Exception as e:
            logger.error(f"❌ [Drive] Upload failed: {e}")
            return UploadResult(
                success=False,
                error_message=str(e)
            )

    def get_direct_link(self, file_id: str) -> str:
        """
        Get direct download link for a file.

        Args:
            file_id: Google Drive file ID

        Returns:
            Direct download URL
        """
        return f"https://drive.google.com/uc?export=view&id={file_id}"
