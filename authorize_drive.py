"""One-time script to authorize Google Drive access."""
from src.infrastructure.drive_service import GoogleDriveService
import os
from dotenv import load_dotenv

load_dotenv()

credentials_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')
folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')

print("Starting OAuth authorization...")
drive = GoogleDriveService(credentials_file=credentials_file, folder_id=folder_id)
print("✅ Authorization complete!")
