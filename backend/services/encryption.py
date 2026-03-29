"""
TenderBot Global — KMS Encryption Service
Provides symmetric E2E encryption for sensitive DB data.
"""
import os
import logging
from cryptography.fernet import Fernet
from backend.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# Fallback static key for development/demo only if not provided in env
# In production, KMS_SECRET_KEY must be stored in HSM or secured Vault
DEV_KEY = b'wz9-c9FpJX4D2rI9wHn6d3M1Wk2kX9_qL8oA9eA3b_g='
key_str = getattr(settings, 'kms_secret_key', None) or os.environ.get("KMS_SECRET_KEY")

if key_str:
    KMS_KEY = key_str.encode()
else:
    logger.warning("No KMS_SECRET_KEY configured. Using default dev key.")
    KMS_KEY = DEV_KEY

fernet = Fernet(KMS_KEY)

def encrypt_text(text: str) -> str:
    """Encrypts text for secure DB storage."""
    try:
        if not text:
            return text
        return fernet.encrypt(text.encode('utf-8')).decode('utf-8')
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        return text

def decrypt_text(encrypted_text: str) -> str:
    """Decrypts text returned from DB."""
    try:
        if not encrypted_text:
            return encrypted_text
        return fernet.decrypt(encrypted_text.encode('utf-8')).decode('utf-8')
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        return encrypted_text
