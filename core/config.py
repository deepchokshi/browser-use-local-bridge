import os
from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Server Configuration
    PORT: int = Field(default=8000, env="PORT")
    HOST: str = Field(default="0.0.0.0", env="HOST")
    LOG_LEVEL: str = Field(default="info", env="LOG_LEVEL")
    DEBUG: bool = Field(default=False, env="DEBUG")
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    
    # API Configuration
    API_V1_PREFIX: str = Field(default="/api/v1", env="API_V1_PREFIX")
    CORS_ORIGINS: str = Field(default="*", env="CORS_ORIGINS")
    
    # AI/LLM Provider Configuration
    DEFAULT_LLM_PROVIDER: str = Field(default="openai", env="DEFAULT_LLM_PROVIDER")
    DEFAULT_MODEL: str = Field(default="gpt-4o-mini", env="DEFAULT_MODEL")
    
    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    OPENAI_BASE_URL: Optional[str] = Field(default=None, env="OPENAI_BASE_URL")
    OPENAI_ORGANIZATION: Optional[str] = Field(default=None, env="OPENAI_ORGANIZATION")
    
    # Azure OpenAI Configuration
    AZURE_OPENAI_API_KEY: Optional[str] = Field(default=None, env="AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_ENDPOINT: Optional[str] = Field(default=None, env="AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_API_VERSION: str = Field(default="2023-12-01-preview", env="AZURE_OPENAI_API_VERSION")
    AZURE_OPENAI_DEPLOYMENT_NAME: Optional[str] = Field(default=None, env="AZURE_OPENAI_DEPLOYMENT_NAME")
    
    # Anthropic Configuration
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    ANTHROPIC_BASE_URL: Optional[str] = Field(default=None, env="ANTHROPIC_BASE_URL")
    
    # Google AI Configuration
    GOOGLE_AI_API_KEY: Optional[str] = Field(default=None, env="GOOGLE_AI_API_KEY")
    GOOGLE_AI_PROJECT_ID: Optional[str] = Field(default=None, env="GOOGLE_AI_PROJECT_ID")
    
    # Mistral AI Configuration
    MISTRAL_API_KEY: Optional[str] = Field(default=None, env="MISTRAL_API_KEY")
    MISTRAL_BASE_URL: Optional[str] = Field(default=None, env="MISTRAL_BASE_URL")
    
    # Ollama Configuration
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    OLLAMA_MODEL: str = Field(default="llama2", env="OLLAMA_MODEL")
    
    # Amazon Bedrock Configuration
    AWS_ACCESS_KEY_ID: Optional[str] = Field(default=None, env="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(default=None, env="AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str = Field(default="us-east-1", env="AWS_REGION")
    BEDROCK_MODEL_ID: str = Field(default="anthropic.claude-3-sonnet-20240229-v1:0", env="BEDROCK_MODEL_ID")
    
    # Browser Configuration
    CHROME_EXECUTABLE_PATH: Optional[str] = Field(default=None, env="CHROME_EXECUTABLE_PATH")
    BROWSER_HEADLESS: bool = Field(default=True, env="BROWSER_HEADLESS")
    BROWSER_USER_DATA_PERSISTENCE: bool = Field(default=True, env="BROWSER_USER_DATA_PERSISTENCE")
    BROWSER_USER_DATA_DIR: str = Field(default="./browser_data", env="BROWSER_USER_DATA_DIR")
    BROWSER_TIMEOUT: int = Field(default=30000, env="BROWSER_TIMEOUT")
    BROWSER_VIEWPORT_WIDTH: int = Field(default=1920, env="BROWSER_VIEWPORT_WIDTH")
    BROWSER_VIEWPORT_HEIGHT: int = Field(default=1080, env="BROWSER_VIEWPORT_HEIGHT")
    
    # Media and Storage Configuration
    MEDIA_DIR: str = Field(default="./media", env="MEDIA_DIR")
    MAX_MEDIA_SIZE_MB: int = Field(default=100, env="MAX_MEDIA_SIZE_MB")
    SCREENSHOT_QUALITY: int = Field(default=90, env="SCREENSHOT_QUALITY")
    ENABLE_SCREENSHOTS: bool = Field(default=True, env="ENABLE_SCREENSHOTS")
    ENABLE_RECORDINGS: bool = Field(default=False, env="ENABLE_RECORDINGS")
    
    # Task Configuration
    MAX_CONCURRENT_TASKS: int = Field(default=5, env="MAX_CONCURRENT_TASKS")
    TASK_TIMEOUT_MINUTES: int = Field(default=30, env="TASK_TIMEOUT_MINUTES")
    DEFAULT_USER_ID: str = Field(default="default_user", env="DEFAULT_USER_ID")
    
    # Database Configuration (for future persistence)
    DATABASE_URL: str = Field(default="sqlite:///./browser_use_local.db", env="DATABASE_URL")
    
    # Security Configuration
    SECRET_KEY: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Telemetry and Monitoring
    TELEMETRY_ENABLED: bool = Field(default=False, env="TELEMETRY_ENABLED")
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")
    SENTRY_DSN: Optional[str] = Field(default=None, env="SENTRY_DSN")
    
    # Redis Configuration (for task queuing)
    REDIS_URL: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    USE_REDIS: bool = Field(default=False, env="USE_REDIS")
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    RATE_LIMIT_WINDOW_SECONDS: int = Field(default=3600, env="RATE_LIMIT_WINDOW_SECONDS")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    def get_cors_origins(self) -> List[str]:
        """Parse CORS origins from string or return default"""
        if isinstance(self.CORS_ORIGINS, str):
            if self.CORS_ORIGINS.startswith('[') and self.CORS_ORIGINS.endswith(']'):
                # Try to parse as JSON array
                try:
                    import json
                    return json.loads(self.CORS_ORIGINS)
                except json.JSONDecodeError:
                    pass
            # Split by comma if it's a comma-separated string
            if ',' in self.CORS_ORIGINS:
                return [origin.strip() for origin in self.CORS_ORIGINS.split(',')]
            # Single origin
            return [self.CORS_ORIGINS]
        return [self.CORS_ORIGINS] if self.CORS_ORIGINS else ["*"]

    def get_ai_provider_config(self, provider: str) -> dict:
        """Get configuration for specific AI provider"""
        configs = {
            "openai": {
                "api_key": self.OPENAI_API_KEY,
                "base_url": self.OPENAI_BASE_URL,
                "organization": self.OPENAI_ORGANIZATION
            },
            "azure_openai": {
                "api_key": self.AZURE_OPENAI_API_KEY,
                "endpoint": self.AZURE_OPENAI_ENDPOINT,
                "api_version": self.AZURE_OPENAI_API_VERSION,
                "deployment_name": self.AZURE_OPENAI_DEPLOYMENT_NAME
            },
            "anthropic": {
                "api_key": self.ANTHROPIC_API_KEY,
                "base_url": self.ANTHROPIC_BASE_URL
            },
            "google": {
                "api_key": self.GOOGLE_AI_API_KEY,
                "project_id": self.GOOGLE_AI_PROJECT_ID
            },
            "mistral": {
                "api_key": self.MISTRAL_API_KEY,
                "base_url": self.MISTRAL_BASE_URL
            },
            "ollama": {
                "base_url": self.OLLAMA_BASE_URL,
                "model": self.OLLAMA_MODEL
            },
            "bedrock": {
                "aws_access_key_id": self.AWS_ACCESS_KEY_ID,
                "aws_secret_access_key": self.AWS_SECRET_ACCESS_KEY,
                "region": self.AWS_REGION,
                "model_id": self.BEDROCK_MODEL_ID
            }
        }
        return configs.get(provider, {})

settings = Settings()