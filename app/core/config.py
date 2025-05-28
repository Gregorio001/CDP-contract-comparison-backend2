import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT")
    OPENAI_API_VERSION: str = os.getenv("OPENAI_API_VERSION", "2024-02-01")
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME: str = os.getenv(
        "AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"
    )
    AZURE_OPENAI_CHAT_DEPLOYMENT_NAME: str = os.getenv(
        "AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"
    )

    # Langchain specific for Azure
    OPENAI_API_TYPE: str = os.getenv("OPENAI_API_TYPE", "azure")

    POSTGRES_USER: str = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB")

    @property
    def DATABASE_URL(self) -> str | None:
        if all(
            [
                self.POSTGRES_USER,
                self.POSTGRES_PASSWORD,
                self.POSTGRES_HOST,
                self.POSTGRES_PORT,
                self.POSTGRES_DB,
            ]
        ):
            return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        return None


settings = Settings()

# Setup environment variables for Langchain Azure OpenAI
os.environ["AZURE_OPENAI_API_KEY"] = settings.AZURE_OPENAI_API_KEY
os.environ["AZURE_OPENAI_ENDPOINT"] = settings.AZURE_OPENAI_ENDPOINT
os.environ["OPENAI_API_VERSION"] = settings.OPENAI_API_VERSION
os.environ["OPENAI_API_TYPE"] = settings.OPENAI_API_TYPE  # Important for Langchain
