from typing import Dict
import os
from pathlib import Path

# Load .env file automatically
try:
    from dotenv import load_dotenv
    # Find .env in project root
    env_path = Path(__file__).parent.parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass  # python-dotenv not installed

class BaseLLMAdapter:
    def __init__(self, model: str, **kwargs):
        self.model = model
        self.kwargs = kwargs
    
    def generate(self, prompt: str) -> Dict:
        raise NotImplementedError

class OpenAIAdapter(BaseLLMAdapter):
    def __init__(self, model: str = "gpt-4", **kwargs):
        super().__init__(model, **kwargs)
        try:
            import openai
            self.client = openai.OpenAI()
        except ImportError:
            raise RuntimeError("pip install openai")
            
    def generate(self, prompt: str) -> Dict:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.kwargs.get('temperature', 0.2),
                max_tokens=self.kwargs.get('max_tokens', 4000)
            )
            return {
                "success": True,
                "code": response.choices[0].message.content,
                "tokens": response.usage.total_tokens
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

class OpenRouterAdapter(BaseLLMAdapter):
    def __init__(self, model: str = "meta-llama/llama-3-8b-instruct", **kwargs):
        super().__init__(model, **kwargs)
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        if not self.api_key:
            raise RuntimeError("Set OPENROUTER_API_KEY")
            
    def generate(self, prompt: str) -> Dict:
        try:
            import requests
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": self.kwargs.get('temperature', 0.2),
                    "max_tokens": self.kwargs.get('max_tokens', 4000)
                }
            )
            if response.status_code != 200:
                return {"success": False, "error": response.text}
                
            result = response.json()
            return {
                "success": True,
                "code": result['choices'][0]['message']['content'],
                "tokens": result['usage']['total_tokens']
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

# Factory
def get_adapter(name: str, model: str = None, **kwargs) -> BaseLLMAdapter:
    if name == "openai":
        return OpenAIAdapter(model or "gpt-4", **kwargs)
    elif name == "openrouter":
        return OpenRouterAdapter(model or "meta-llama/llama-3-8b-instruct", **kwargs)
    else:
        raise ValueError(f"Unknown adapter: {name}")
