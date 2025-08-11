#!/usr/bin/env python3
"""
Script para gerar uma nova Django SECRET_KEY.
"""

import secrets
import string


def generate_secret_key(length=50):
    """Generate a secure Django SECRET_KEY."""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    # Remove characters that might cause issues in .env files
    alphabet = alphabet.replace('"', '').replace("'", '').replace('\\', '')
    
    secret_key = ''.join(secrets.choice(alphabet) for _ in range(length))
    return secret_key


if __name__ == "__main__":
    print("Nova Django SECRET_KEY gerada:")
    print(f"SECRET_KEY={generate_secret_key()}")
    print("\nCopie esta linha para seu arquivo .env") 