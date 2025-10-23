import modal
import os

DEPENDENCIES = [
    "httpx>=0.28.1",
    "modal>=1.1.4",
    "pydantic>=2.11.9",
    "pydantic-ai>=1.2.1",
    "supabase>=2.21.1",
]
ENV = os.getenv("ENV", "development")
SECRETS = [modal.Secret.from_name(f"fumiko-scraper-{ENV}")]

image = modal.Image.debian_slim(python_version="3.12").pip_install(*DEPENDENCIES)
app = modal.App(name="fumiko-scraper", image=image, secrets=SECRETS)
