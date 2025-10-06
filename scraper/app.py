import modal
import os

DEPENDENCIES = [
    "httpx==0.28.1",
    "pydantic>=2.11.9",
    "supabase>=2.21.1",
]
ENV = os.getenv("ENV", "development")
SECRETS = [modal.Secret.from_name(f"malaina-scraper-{ENV}")]

image = modal.Image.debian_slim(python_version="3.12").pip_install(*DEPENDENCIES)
app = modal.App(name="malaina-scraper", image=image, secrets=SECRETS)
