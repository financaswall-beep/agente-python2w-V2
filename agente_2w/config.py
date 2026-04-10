import os
from dotenv import load_dotenv

load_dotenv(override=True)

SUPABASE_URL: str = os.environ["SUPABASE_URL"]
SUPABASE_KEY: str = os.environ["SUPABASE_KEY"]

OPENAI_API_KEY: str = os.environ["OPENAI_API_KEY"]
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")

# Chatwoot
CHATWOOT_BASE_URL: str = os.getenv("CHATWOOT_BASE_URL", "").rstrip("/")
CHATWOOT_API_TOKEN: str = os.getenv("CHATWOOT_API_TOKEN", "")
CHATWOOT_ACCOUNT_ID: str = os.getenv("CHATWOOT_ACCOUNT_ID", "1")

# Limites de execucao
MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "2"))
MAX_TOOL_ROUNDS: int = int(os.getenv("MAX_TOOL_ROUNDS", "5"))
