"""
Module for handling credential storage and retrieval.
"""
import json
import os
import logging


class CredentialManager:
    """Handles saving and loading of user credentials."""
    
    def __init__(self, credentials_file='credentials.json'):
        self.credentials_file = credentials_file
        self.logger = logging.getLogger(__name__)

    def save_credentials(self, url, username, password, save_credentials_flag):
        """Save credentials to a file"""
        if save_credentials_flag:
            creds = {
                'url': url,
                'username': username,
                # Note: Storing passwords in plain text is not secure for production use
                'password': password
            }
            with open(self.credentials_file, 'w') as f:
                json.dump(creds, f)
        else:
            # If unchecked, remove saved credentials
            if os.path.exists(self.credentials_file):
                os.remove(self.credentials_file)

    def load_saved_credentials(self):
        """Load saved credentials from file"""
        try:
            if os.path.exists(self.credentials_file):
                with open(self.credentials_file, 'r') as f:
                    creds = json.load(f)
                    return (
                        creds.get('url', ''),
                        creds.get('username', ''),
                        creds.get('password', ''),
                        True  # Check the box since we have saved creds
                    )
            else:
                # Set default URL if no saved credentials
                return "https://your-nextcloud-url.com/remote.php/dav/", "", "", False
        except Exception as e:
            self.logger.error(f"Error loading saved credentials: {e}", exc_info=True)
            return "https://your-nextcloud-url.com/remote.php/dav/", "", "", False