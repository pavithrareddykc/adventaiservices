import os
from typing import Optional


def load_env_file(path: str = ".env") -> None:
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                # Remove optional surrounding quotes
                value = value.strip().strip('"').strip('\'')
                if key and key not in os.environ:
                    os.environ[key] = value
    except Exception:
        # Ignore env file errors silently
        pass