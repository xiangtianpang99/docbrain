from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import os
from langchain_community.chat_models import ChatOpenAI
from crewai import LLM

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def get_langchain_llm(self, config: Dict[str, Any]) -> Any:
        """Create and return a LangChain ChatModel."""
        pass

    @abstractmethod
    def get_crew_llm(self, config: Dict[str, Any]) -> Any:
        """Create and return a CrewAI LLM instance."""
        pass

class DeepSeekProvider(LLMProvider):
    def get_langchain_llm(self, config: Dict[str, Any]) -> Any:
        api_key = config.get("api_key")
        base_url = config.get("base_url", "https://api.deepseek.com")
        model = config.get("model", "deepseek-chat")
        
        if not api_key:
             # Fallback to env var if not in config
             api_key = os.getenv("DEEPSEEK_API_KEY")

        return ChatOpenAI(
            model_name=model,
            temperature=0.7,
            openai_api_key=api_key,
            openai_api_base=base_url
        )

    def get_crew_llm(self, config: Dict[str, Any]) -> Any:
        api_key = config.get("api_key")
        base_url = config.get("base_url", "https://api.deepseek.com")
        model = config.get("model", "deepseek-chat")
        
        if not api_key:
             api_key = os.getenv("DEEPSEEK_API_KEY")

        # CrewAI LLM wrapper expects model looking like "openai/model_name" for custom OpenAI-compatible endpoints sometimes,
        # or just provider specific structure.
        # For DeepSeek via OpenAI protocol, we usually use "openai/deepseek-chat" pattern in CrewAI to force OpenAI client usage.
        
        return LLM(
            model=f"openai/{model}", 
            base_url=base_url,
            api_key=api_key
        )

class OpenAIProvider(LLMProvider):
    def get_langchain_llm(self, config: Dict[str, Any]) -> Any:
        api_key = config.get("api_key")
        base_url = config.get("base_url", "https://api.openai.com/v1")
        model = config.get("model", "gpt-4")

        return ChatOpenAI(
            model_name=model,
            temperature=0.7,
            openai_api_key=api_key,
            openai_api_base=base_url
        )

    def get_crew_llm(self, config: Dict[str, Any]) -> Any:
        api_key = config.get("api_key")
        # CrewAI defaults to OpenAI, so we can just pass the model
        model = config.get("model", "gpt-4")
        
        return LLM(
            model=model,
            api_key=api_key
        )

class OllamaProvider(LLMProvider):
    def get_langchain_llm(self, config: Dict[str, Any]) -> Any:
        base_url = config.get("base_url", "http://localhost:11434")
        model = config.get("model", "llama3")
        
        # We use ChatOpenAI compatible client for Ollama to keep consistency
        # Assuming Ollama is running safely locally
        return ChatOpenAI(
            model_name=model,
            temperature=0.7,
            openai_api_key="ollama", # Ollama doesn't need a real key usually
            openai_api_base=f"{base_url}/v1"
        )

    def get_crew_llm(self, config: Dict[str, Any]) -> Any:
        base_url = config.get("base_url", "http://localhost:11434")
        model = config.get("model", "llama3")
        
        return LLM(
            model=f"openai/{model}",
            base_url=f"{base_url}/v1",
            api_key="ollama"
        )

class LLMFactory:
    _providers = {
        "deepseek": DeepSeekProvider(),
        "openai": OpenAIProvider(),
        "ollama": OllamaProvider(),
        "custom": OpenAIProvider() # Custom usually implies OpenAI-compatible
    }

    @staticmethod
    def get_provider(name: str) -> LLMProvider:
        provider = LLMFactory._providers.get(name.lower())
        if not provider:
            raise ValueError(f"Unknown LLM provider: {name}")
        return provider

    @staticmethod
    def create_langchain_llm(config_manager) -> Any:
        """
        Create a LangChain LLM based on the active configuration.
        """
        active_provider_name = config_manager.get("active_provider", "deepseek")
        providers_config = config_manager.get("llm_providers", {})
        provider_config = providers_config.get(active_provider_name, {})
        
        provider = LLMFactory.get_provider(active_provider_name)
        return provider.get_langchain_llm(provider_config)

    @staticmethod
    def create_crew_llm(config_manager) -> Any:
        """
        Create a CrewAI LLM based on the active configuration.
        """
        active_provider_name = config_manager.get("active_provider", "deepseek")
        providers_config = config_manager.get("llm_providers", {})
        provider_config = providers_config.get(active_provider_name, {})
        
        provider = LLMFactory.get_provider(active_provider_name)
        return provider.get_crew_llm(provider_config)
