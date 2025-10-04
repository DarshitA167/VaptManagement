#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path
import dotenv

BASE_DIR = Path(__file__).resolve().parent
dotenv_path = BASE_DIR / ".env"
if dotenv_path.exists():
    dotenv.load_dotenv(dotenv_path)

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vaptmanagement.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django..."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
