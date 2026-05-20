"""GLM (Zhipu AI) provider implementation."""

from __future__ import annotations

from typing import Any, Optional

try:
    from openai import OpenAI  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    OpenAI = None

from .openai_compatible import OpenAICompatibleProvider


class GLMProvider(OpenAICompatibleProvider):
    """GLM (Zhipu AI) provider using its OpenAI-compatible API.

    GLM models on z.ai require the 'zai/' prefix in model names.
    """

    DEFAULT_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"

    def __init__(
        self, api_key: str, base_url: Optional[str] = None, model: Optional[str] = None
    ):
        """Initialize GLM provider.

        Args:
            api_key: Zhipu AI API key
            base_url: Base URL (optional)
            model: Default model (default: zai/glm-5)
        """
        super().__init__(api_key, base_url or self.DEFAULT_BASE_URL, model or "zai/glm-5")

    def _create_client(self) -> Any:
        """Create OpenAI-compatible client for GLM."""
        if OpenAI is None:  # pragma: no cover
            raise ModuleNotFoundError(
                "openai package is not installed. Install core dependencies to use GLMProvider."
            )
        return OpenAI(api_key=self.api_key, base_url=self.base_url)

    def get_available_models(self) -> list[str]:
        """Get list of available GLM models.

        Returns:
            List of model names (with zai/ prefix for z.ai API)
        """
        return [
            # GLM-5 series (latest, requires zai/ prefix)
            "zai/glm-5",
            "zai/glm-5-turbo",
            # GLM-4 series (standard, zai/ prefix)
            "zai/glm-4",
            "zai/glm-4-plus",
            "zai/glm-4-air",
            "zai/glm-4-flash",
            "zai/glm-4.5",
            "zai/glm-4.6",
            "zai/glm-4.7",
            # GLM-3 series (legacy)
            "zai/glm-3-turbo",
        ]
