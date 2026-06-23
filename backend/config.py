from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    host: str = "127.0.0.1"
    port: int = 8000
    max_iterations: int = 250

    # Tell Pydantic to ignore extra variables in the .env file
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()

# Supported providers and their OpenAI-compatible base URLs
PROVIDERS = {
    "NVIDIA": {
        "base_url": "https://integrate.api.nvidia.com/v1",
        "key_prefix": "nvapi-",
        "models": [
            "minimaxai/minimax-m3",
            "moonshotai/kimi-k2.6",
            "mistralai/mistral-medium-3.5-128b",
            "z-ai/glm-5.1",
            "minimaxai/minimax-m2.7",
            "qwen/qwen3.5-122b-a10b",
            "google/gemma-4-31b-it",
            "deepseek-ai/deepseek-v4-flash",
            "deepseek-ai/deepseek-v4-pro",
            "openai/gpt-oss-20b",
            "openai/gpt-oss-120b",
            "meta/llama-3.3-70b-instruct"
        ]
    },
    "Groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "key_prefix": "gsk_",
        "models": [
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
            "qwen/qwen3-32b",
            "qwen/qwen3.6-27b",
        ]
    },
    "OpenAI": {
        "base_url": "https://api.openai.com/v1",
        "key_prefix": "sk-",
        "models": [
            "gpt-4o",
            "gpt-4o-mini"
        ]
    },
    "Gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "key_prefix": "AIza",
        "models": [
            "gemini-3.5-flash",
            "gemini-3.5-pro",
            "gemini-3.1-pro",
            "gemini-3.1-flash-lite",
            "gemini-2.5-pro",
            "gemini-2.5-flash",
            "gemini-3.1-flash-live-preview",
            "gemini-3.1-flash-tts-preview",
            "text-embedding-004",
            "gemma-4"
        ]
    },
    "OpenRouter": { # OpenRouter gives access to Anthropic/Claude models!
        "base_url": "https://openrouter.ai/api/v1",
        "key_prefix": "sk-or-",
        "models": [
            "nvidia/nemotron-3-ultra-550b-a55b:free",
            "poolside/laguna-m.1:free",
            "nvidia/nemotron-3-super-120b-a12b:free",
            "openai/gpt-oss-120b:free",
            "poolside/laguna-xs.2:free",
            "openai/gpt-oss-20b:free",
            "google/gemma-4-31b-it:free",
            "nvidia/nemotron-3-nano-30b-a3b:free",
            "cohere/north-mini-code:free",
            "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
            "nvidia/nemotron-nano-9b-v2:free",
            "nvidia/nemotron-nano-12b-v2-vl:free",
            "google/gemma-4-26b-a4b-it:free",
            "liquid/lfm-2.5-1.2b-thinking:free",
            "liquid/lfm-2.5-1.2b-instruct:free",
            "nvidia/nemotron-3.5-content-safety:free",
            "qwen/qwen3-next-80b-a3b-instruct:free",
            "meta-llama/llama-3.3-70b-instruct:free",
            "cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
            "meta-llama/llama-3.2-3b-instruct:free",
            "nousresearch/hermes-3-llama-3.1-405b:free",
            "openrouter/free",
            "qwen/qwen3-coder:free"
        ]
    }
}