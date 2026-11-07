"""Reusable Asynchronous Ollama Client."""
from typing import Any, Dict, List, Optional
import httpx
from app.core.config import settings
from app.core.logging import logger


class OllamaClient:
    """Asynchronous client for interacting with local Ollama API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout = timeout or settings.OLLAMA_TIMEOUT_SECONDS

    async def check_connectivity(self) -> Dict[str, Any]:
        """Checks if Ollama server is reachable and inspects installed models."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    models = [m.get("name") for m in data.get("models", [])]
                    model_found = any(self.model in m for m in models)
                    return {
                        "connected": True,
                        "base_url": self.base_url,
                        "target_model": self.model,
                        "model_available": model_found,
                        "installed_models": models,
                    }
                return {
                    "connected": False,
                    "error": f"Ollama returned HTTP {res.status_code}",
                }
        except httpx.ConnectError:
            return {
                "connected": False,
                "error": f"Cannot connect to Ollama at {self.base_url}. Service may be stopped.",
            }
        except httpx.TimeoutException:
            return {
                "connected": False,
                "error": f"Connection to {self.base_url} timed out.",
            }
        except Exception as exc:
            return {
                "connected": False,
                "error": str(exc),
            }

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """Sends asynchronous chat request to Ollama with timeout safety."""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_ctx": 2048,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(f"{self.base_url}/api/chat", json=payload)
                if res.status_code == 200:
                    return res.json()
                raise RuntimeError(f"Ollama returned HTTP {res.status_code}: {res.text}")
        except httpx.ConnectError as ce:
            raise ConnectionError(f"Failed to connect to Ollama at {self.base_url}: {ce}")
        except httpx.TimeoutException:
            raise TimeoutError(f"Ollama inference timed out after {self.timeout}s.")
