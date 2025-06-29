# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "mistralai/mistral-small-3.2-24b-instruct:free"  # puoi cambiarlo con un altro modello gratuito

if not HUGGINGFACE_API_KEY:
    raise RuntimeError("❌ La variabile HUGGINGFACE_API_KEY non è definita!")
