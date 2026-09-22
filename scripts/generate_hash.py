"""
Run this once to generate a bcrypt hash for Astra's password, then paste
the output into .env as ASTRA_PASSWORD_HASH.

Usage:
    python scripts/generate_hash.py "your-chosen-password"
"""

import sys
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print('Usage: python scripts/generate_hash.py "your-chosen-password"')
        sys.exit(1)

    password = sys.argv[1]
    print(pwd_context.hash(password))
