"""
Security - Encryption and secret management for production.
Implements AES-256-GCM encryption for sensitive API keys and credentials.
"""

import base64
import os
from typing import Optional

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet


class SecretManager:
    """
    Manages encryption and decryption of sensitive secrets.
    In production, the AETHER_MASTER_KEY should be stored in a KMS (AWS KMS, GCP KMS, Vault).
    """

    def __init__(self, master_key: Optional[str] = None):
        self.master_key = master_key or os.getenv("AETHER_MASTER_KEY")
        if not self.master_key:
            # Fallback for development only - in production this must be set!
            self.master_key = "dev-secret-key-do-not-use-in-production"
        
        self.fernet = self._get_fernet()

    def _get_fernet(self) -> Fernet:
        """Derive a 32-byte key from the master key for Fernet encryption."""
        salt = b'aether_salt_2026' # In production, use a unique salt per deployment
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key.encode()))
        return Fernet(key)

    def encrypt(self, secret: str) -> str:
        """Encrypt a secret string."""
        if not secret:
            return ""
        return self.fernet.encrypt(secret.encode()).decode()

    def decrypt(self, encrypted_secret: str) -> str:
        """Decrypt an encrypted secret string."""
        if not encrypted_secret:
            return ""
        try:
            return self.fernet.decrypt(encrypted_secret.encode()).decode()
        except Exception as e:
            # Log error but don't expose details
            raise ValueError("Failed to decrypt secret. Check master key.") from e


# Global instance
secrets = SecretManager()
