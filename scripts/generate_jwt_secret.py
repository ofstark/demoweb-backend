"""
Run this once to generate a random JWT signing secret, then paste the
output into .env as JWT_SECRET_KEY.

Usage:
    python scripts/generate_jwt_secret.py
"""

import secrets

if __name__ == "__main__":
    print(secrets.token_urlsafe(48))
