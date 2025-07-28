"""
title: Pollinations
author: #
email: #
date: 2025-06-18
version: 1.2
license: #
description: AI Image generations using Pollinations.ai.
"""

import httpx
from typing import Awaitable, Callable, Dict, Tuple


class Tools:
    """
    A class to generate images using the Pollinators.ai API.
    """

    BASE_URL = "https://image.pollinations.ai/prompt/"

    FORMATS: Dict[str, Tuple[int, int]] = {
        "default": (1920, 1080),
        "square": (1080, 1080),
        "landscape": (1920, 1080),
        "landscape_large": (2560, 1440),
        "portrait": (1080, 1920),
        "portrait_large": (1440, 2560),
    }

    def __init__(self):
        """
        Initializes the Tools class and a persistent httpx.AsyncClient for performance.
        """
        self.client = httpx.AsyncClient()

    async def _emit_status(
        self, event_emitter, status: str, description: str, done: bool
    ):
        """Helper function to emit status updates."""
        # The event_emitter is expected to be a callable, async function.
        await event_emitter(
            {
                "data": {"description": description, "status": status, "done": done},
                "type": "status",
            }
        )

    async def create_image(
        self,
        prompt: str,
        __event_emitter__,  # <-- CRITICAL CHANGE: Type hint removed to prevent Pydantic JSON Schema error.
        image_format: str = "default",
        model: str = "flux",
        enhance: bool = True,
        seed: int = 42,
    ) -> str:
        """
        Asynchronously generates an image based on a prompt.

        Args:
            prompt: The text prompt to generate the image from.
            __event_emitter__: An asynchronous function to emit status events.
            image_format: The desired aspect ratio of the image.
            model: The AI model to use for generation.
            enhance: If True, applies prompt enhancement.
            seed: A seed for the random number generator for reproducibility.

        Returns:
            A Markdown string with the URL of the generated image on success,
            or an error message on failure.
        """
        event_emitter = __event_emitter__
        await self._emit_status(
            event_emitter, "in_progress", "Image generation started...", False
        )

        if image_format not in self.FORMATS:
            error_msg = f"Invalid aspect ratio: '{image_format}'. Please use one of: {list(self.FORMATS.keys())}"
            await self._emit_status(event_emitter, "complete", error_msg, True)
            return error_msg

        width, height = self.FORMATS[image_format]

        params = {
            "width": width,
            "height": height,
            "model": model,
            "nologo": "true",
            "enhance": str(enhance).lower(),
            "seed": seed,
        }

        url_path_safe_prompt = httpx.URL(prompt).path
        url = f"{self.BASE_URL}{url_path_safe_prompt}"

        try:
            response = await self.client.get(url, params=params, timeout=120.0)
            response.raise_for_status()
            image_url = str(response.url)

            await self._emit_status(
                event_emitter, "complete", "Image generation successful!", True
            )
            return f"![{prompt}]({image_url})"

        except httpx.HTTPStatusError as e:
            error_msg = (
                f"API Error: {e.response.status_code} - The server returned an error."
            )
            await self._emit_status(event_emitter, "complete", error_msg, True)
            return error_msg
        except httpx.RequestError as e:
            error_msg = f"Network error while requesting the image: {str(e)}"
            await self._emit_status(event_emitter, "complete", error_msg, True)
            return error_msg
        except Exception as e:
            error_msg = f"An unexpected error occurred: {str(e)}"
            await self._emit_status(event_emitter, "complete", error_msg, True)
            return error_msg

    async def aclose(self):
        """
        Closes the underlying httpx.AsyncClient session.
        This should be called when the tool is no longer needed to release resources.
        """
        await self.client.aclose()
