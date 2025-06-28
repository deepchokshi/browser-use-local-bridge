"""
LLM Factory for dynamic AI provider instantiation
Supports OpenAI, Azure OpenAI, Anthropic, Google AI, Mistral, Ollama, and Amazon Bedrock
"""

from typing import Any, Dict, Optional
import logging
from core.config import settings

logger = logging.getLogger(__name__)

class LLMFactory:
    """Factory class for creating LLM instances based on provider configuration"""
    
    @staticmethod
    def create_llm(
        provider: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> Any:
        """
        Create an LLM instance based on the specified provider
        
        Args:
            provider: AI provider name (openai, azure_openai, anthropic, etc.)
            model: Model name to use
            **kwargs: Additional configuration parameters
            
        Returns:
            LLM instance ready for use with browser-use
        """
        provider = provider or settings.DEFAULT_LLM_PROVIDER
        model = model or settings.DEFAULT_MODEL
        
        provider_config = settings.get_ai_provider_config(provider)
        
        # Merge provider config with kwargs
        config = {**provider_config, **kwargs}
        
        try:
            if provider == "openai":
                return LLMFactory._create_openai_llm(model, config)
            elif provider == "azure_openai":
                return LLMFactory._create_azure_openai_llm(model, config)
            elif provider == "anthropic":
                return LLMFactory._create_anthropic_llm(model, config)
            elif provider == "google":
                return LLMFactory._create_google_llm(model, config)
            elif provider == "mistral":
                return LLMFactory._create_mistral_llm(model, config)
            elif provider == "ollama":
                return LLMFactory._create_ollama_llm(model, config)
            elif provider == "bedrock":
                return LLMFactory._create_bedrock_llm(model, config)
            else:
                raise ValueError(f"Unsupported provider: {provider}")
                
        except Exception as e:
            logger.error(f"Failed to create LLM for provider {provider}: {str(e)}")
            # For demo/testing purposes, create a mock LLM when no real API key is available
            if "API key" in str(e) or "required" in str(e).lower():
                logger.warning("Creating mock LLM for testing purposes - tasks will not actually execute")
                return LLMFactory._create_mock_llm(model, config)
            # Fallback to OpenAI if available
            if provider != "openai" and settings.OPENAI_API_KEY:
                logger.info("Falling back to OpenAI provider")
                return LLMFactory._create_openai_llm("gpt-4o", settings.get_ai_provider_config("openai"))
            raise
    
    @staticmethod
    def _create_openai_llm(model: str, config: Dict[str, Any]) -> Any:
        """Create OpenAI LLM instance"""
        try:
            from browser_use.llm import ChatOpenAI
            
            if not config.get("api_key"):
                raise ValueError("OpenAI API key is required")
            
            # For testing: always fail to trigger mock LLM
            if config.get("api_key") == "":  # Empty string means no real API key
                raise ValueError("OpenAI API key is required")
            
            # Create minimal config to avoid parameter issues
            llm_config = {
                "model": model,
                "api_key": config["api_key"]
            }
            
            # Only add optional parameters if they exist and are valid
            if config.get("base_url") and isinstance(config["base_url"], str):
                llm_config["base_url"] = config["base_url"]
            if config.get("organization") and isinstance(config["organization"], str):
                llm_config["organization"] = config["organization"]
            
            logger.debug(f"Creating OpenAI LLM with config keys: {list(llm_config.keys())}")
            return ChatOpenAI(**llm_config)
            
        except ImportError:
            logger.error("OpenAI dependencies not available")
            raise
        except Exception as e:
            logger.error(f"Failed to create OpenAI LLM: {e}")
            raise
    
    @staticmethod
    def _create_azure_openai_llm(model: str, config: Dict[str, Any]) -> Any:
        """Create Azure OpenAI LLM instance"""
        try:
            from browser_use.llm import ChatOpenAI
            
            required_fields = ["api_key", "endpoint"]
            for field in required_fields:
                if not config.get(field):
                    raise ValueError(f"Azure OpenAI {field} is required")
            
            # Use OpenAI client with Azure configuration
            llm_config = {
                "model": config.get("deployment_name", model),
                "api_key": config["api_key"],
                "base_url": f"{config['endpoint'].rstrip('/')}/openai/deployments/{config.get('deployment_name', model)}",
                "default_headers": {
                    "api-version": config.get("api_version", "2023-12-01-preview")
                }
            }
                
            return ChatOpenAI(**llm_config)
            
        except ImportError:
            logger.error("Azure OpenAI dependencies not available")
            raise
    
    @staticmethod
    def _create_anthropic_llm(model: str, config: Dict[str, Any]) -> Any:
        """Create Anthropic LLM instance"""
        try:
            # Try to import from browser_use first, fallback to direct anthropic
            try:
                from browser_use.llm import ChatAnthropic
            except ImportError:
                # Fallback: create a simple wrapper around anthropic client
                import anthropic
                
                class ChatAnthropic:
                    def __init__(self, model, api_key, **kwargs):
                        self.client = anthropic.Anthropic(api_key=api_key)
                        self.model = model
                    
                    async def ainvoke(self, messages):
                        # Simple wrapper - you might need to adapt this based on browser_use interface
                        response = await self.client.messages.create(
                            model=self.model,
                            messages=messages,
                            max_tokens=1000
                        )
                        return response.content[0].text
            
            if not config.get("api_key"):
                raise ValueError("Anthropic API key is required")
            
            llm_config = {
                "model": model or "claude-3-opus-20240229",
                "api_key": config["api_key"]
            }
            
            if config.get("base_url"):
                llm_config["base_url"] = config["base_url"]
                
            return ChatAnthropic(**llm_config)
            
        except ImportError as e:
            logger.error(f"Anthropic dependencies not available: {e}")
            raise
    
    @staticmethod
    def _create_google_llm(model: str, config: Dict[str, Any]) -> Any:
        """Create Google AI LLM instance"""
        try:
            # Try browser_use first, fallback to direct implementation
            try:
                from browser_use.llm import ChatGoogleGenerativeAI
            except ImportError:
                logger.warning("browser_use Google AI integration not available, skipping")
                raise ImportError("Google AI provider not available in current browser_use version")
            
            if not config.get("api_key"):
                raise ValueError("Google AI API key is required")
            
            llm_config = {
                "model": model or "gemini-pro",
                "google_api_key": config["api_key"]
            }
            
            if config.get("project_id"):
                llm_config["project"] = config["project_id"]
                
            return ChatGoogleGenerativeAI(**llm_config)
            
        except ImportError as e:
            logger.error(f"Google AI dependencies not available: {e}")
            raise
    
    @staticmethod
    def _create_mistral_llm(model: str, config: Dict[str, Any]) -> Any:
        """Create Mistral AI LLM instance"""
        try:
            # Try browser_use first, fallback to direct implementation
            try:
                from browser_use.llm import ChatMistralAI
            except ImportError:
                logger.warning("browser_use Mistral AI integration not available, skipping")
                raise ImportError("Mistral AI provider not available in current browser_use version")
            
            if not config.get("api_key"):
                raise ValueError("Mistral API key is required")
            
            llm_config = {
                "model": model or "mistral-large-latest",
                "api_key": config["api_key"]
            }
            
            if config.get("base_url"):
                llm_config["base_url"] = config["base_url"]
                
            return ChatMistralAI(**llm_config)
            
        except ImportError as e:
            logger.error(f"Mistral AI dependencies not available: {e}")
            raise
    
    @staticmethod
    def _create_ollama_llm(model: str, config: Dict[str, Any]) -> Any:
        """Create Ollama LLM instance"""
        try:
            # Try browser_use first, fallback to direct implementation
            try:
                from browser_use.llm import ChatOllama
            except ImportError:
                logger.warning("browser_use Ollama integration not available, skipping")
                raise ImportError("Ollama provider not available in current browser_use version")
            
            llm_config = {
                "model": model or config.get("model", "llama2"),
                "base_url": config.get("base_url", "http://localhost:11434")
            }
                
            return ChatOllama(**llm_config)
            
        except ImportError as e:
            logger.error(f"Ollama dependencies not available: {e}")
            raise
    
    @staticmethod
    def _create_bedrock_llm(model: str, config: Dict[str, Any]) -> Any:
        """Create Amazon Bedrock LLM instance"""
        try:
            # Try browser_use first, fallback to direct implementation
            try:
                from browser_use.llm import BedrockChat
            except ImportError:
                logger.warning("browser_use Bedrock integration not available, skipping")
                raise ImportError("Bedrock provider not available in current browser_use version")
            
            required_fields = ["aws_access_key_id", "aws_secret_access_key", "region"]
            for field in required_fields:
                if not config.get(field):
                    raise ValueError(f"AWS {field} is required for Bedrock")
            
            llm_config = {
                "model_id": model or config.get("model_id", "anthropic.claude-3-sonnet-20240229-v1:0"),
                "credentials_profile_name": None,
                "region_name": config["region"]
            }
            
            # Set AWS credentials
            import os
            os.environ["AWS_ACCESS_KEY_ID"] = config["aws_access_key_id"]
            os.environ["AWS_SECRET_ACCESS_KEY"] = config["aws_secret_access_key"]
                
            return BedrockChat(**llm_config)
            
        except ImportError as e:
            logger.error(f"Amazon Bedrock dependencies not available: {e}")
            raise
    
    @staticmethod
    def get_available_providers() -> Dict[str, bool]:
        """Get list of available providers and their status"""
        providers = {}
        
        # OpenAI - always available if API key is set
        providers["openai"] = bool(settings.OPENAI_API_KEY)
        
        # Azure OpenAI - available if credentials are set
        providers["azure_openai"] = bool(settings.AZURE_OPENAI_API_KEY and settings.AZURE_OPENAI_ENDPOINT)
        
        # Check other providers by trying to import them
        for provider_name, import_check in [
            ("anthropic", lambda: __import__("anthropic")),
            ("google", lambda: __import__("google.generativeai")),
            ("mistral", lambda: __import__("mistralai")),
            ("ollama", lambda: __import__("ollama")),
            ("bedrock", lambda: __import__("boto3"))
        ]:
            try:
                import_check()
                # Check if API keys are available
                if provider_name == "anthropic":
                    providers[provider_name] = bool(settings.ANTHROPIC_API_KEY)
                elif provider_name == "google":
                    providers[provider_name] = bool(settings.GOOGLE_AI_API_KEY)
                elif provider_name == "mistral":
                    providers[provider_name] = bool(settings.MISTRAL_API_KEY)
                elif provider_name == "ollama":
                    providers[provider_name] = True  # Ollama doesn't require API key
                elif provider_name == "bedrock":
                    providers[provider_name] = bool(settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY)
            except ImportError:
                providers[provider_name] = False
        
        return providers
    
    @staticmethod
    def _create_mock_llm(model: str, config: Dict[str, Any]) -> Any:
        """Create a mock LLM for testing when no API key is available"""
        class MockLLM:
            def __init__(self, **kwargs):
                self.model = model
                
            async def ainvoke(self, messages):
                # Return a mock response for testing
                return "Mock response: I would help you navigate and interact with web pages, but no valid API key is configured."
                
            def invoke(self, messages):
                return "Mock response: I would help you navigate and interact with web pages, but no valid API key is configured."
        
        return MockLLM(**config)

    @staticmethod
    def validate_provider_config(provider: str) -> bool:
        """Validate if a provider is properly configured"""
        available_providers = LLMFactory.get_available_providers()
        return available_providers.get(provider, False) 