import os
import shutil
from pathlib import Path
from backend.core.config import settings

def save_upload_file(uploaded_file) -> str:
    """
    Saves a Streamlit uploaded file to the local directory.
    
    Args:
        uploaded_file: The Streamlit uploaded file object
        
    Returns:
        str: The absolute path to the saved file
    """
    file_path = os.path.join(settings.UPLOAD_DIR, uploaded_file.name)
    with open(file_path, "wb") as buffer:
        buffer.write(uploaded_file.getbuffer())
        
    return str(Path(file_path).absolute())

def clean_upload_dir():
    """
    Cleans up the upload directory to remove old files.
    """
    if os.path.exists(settings.UPLOAD_DIR):
        for filename in os.listdir(settings.UPLOAD_DIR):
            file_path = os.path.join(settings.UPLOAD_DIR, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")
