"""
title: Hugging Face Image Generator
description: Generates images from text prompts using HuggingFace's Inference API
author: TheBlackCat98
version: 0.2.0
requirements: huggingface_hub, Pillow
"""


import base64
from pydantic import BaseModel, Field
import logging
from huggingface_hub import InferenceClient
from io import BytesIO
from PIL import Image

# Import CACHE_DIR from your backend configuration so it matches the static files mount.
from open_webui.config import CACHE_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HFException(Exception):
    """Base exception for HuggingFace API related errors."""

    pass


class Tools:
    class Valves(BaseModel):
        HF_API_KEY: str = Field(
            default=None,
            description="HuggingFace API key for accessing the serverless endpoints",
        )
        MODEL_NAME: str = Field(
            default="stabilityai/stable-diffusion-3.5-large-turbo",
            description="HuggingFace model name for text-to-image generation",
        )

    def __init__(self):
        self.valves = self.Valves()
        self.client = None
        
    async def _get_client(self):
        if not self.client:
            if not self.valves.HF_API_KEY:
                raise ValueError("HuggingFace API key is not set in the Valves.")
            self.client = InferenceClient(
                provider="auto",
                api_key=self.valves.HF_API_KEY
            )
        return self.client

    async def _emit_status(
        self, event_emitter, status: str, description: str, done: bool
    ):
        """Helper function to emit status updates."""
        if event_emitter:
            await event_emitter(
                {
                    "type": "status",
                    "data": {"description": description, "status": status, "done": done},
                }
            )

    async def create_image(
        self,
        prompt: str,
        __event_emitter__=None,
        image_format: str = "default",
        model: str = None,
        seed: int = 42,
    ) -> str:
        """
        Asynchronously generates an image based on a prompt.

        Args:
            prompt: The text prompt to generate the image from.
            __event_emitter__: An asynchronous function to emit status events.
            image_format: The desired aspect ratio of the image.
            model: The AI model to use for generation (defaults to self.valves.MODEL_NAME).
            seed: A seed for the random number generator for reproducibility.

        Returns:
            A Markdown string with the URL of the generated image on success,
            or an error message on failure.
        """
        event_emitter = __event_emitter__
        await self._emit_status(
            event_emitter, "in_progress", "Image generation started...", False
        )
        # Initialize client
        try:
            client = await self._get_client()
        except ValueError as e:
            error_msg = str(e)
            await self._emit_status(event_emitter, "complete", f"Error: {error_msg}", True)
            return error_msg

        # Set image dimensions
        formats = {
            "default": (1024, 1024),
            "square": (1024, 1024),
            "landscape": (1024, 768),
            "landscape_large": (1440, 1024),
            "portrait": (768, 1024),
            "portrait_large": (1024, 1440),
        }

        if image_format not in formats:
            error_msg = f"Invalid format. Must be one of: {', '.join(formats.keys())}"
            await self._emit_status(event_emitter, "complete", error_msg, True)
            return error_msg

        width, height = formats[image_format]
        model = model or self.valves.MODEL_NAME

        try:
            await self._emit_status(
                event_emitter, "in_progress", "Generating image...", False
            )

            # Generate the image
            image = client.text_to_image(
                prompt=prompt,
                model=model,
                width=width,
                height=height
            )
            
            # Convert image to base64
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            # Create a data URL for the image
            image_url = f"data:image/png;base64,{img_str}"

            await self._emit_status(
                event_emitter, "complete", "Image generated successfully!", True
            )
            
            # Return simple markdown with the image
            return f"![{prompt}]({image_url})"

        except Exception as e:
            error_msg = f"Error generating image: {str(e)}"
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                error_msg += f" - {e.response.text}"
            await self._emit_status(event_emitter, "complete", error_msg, True)
            return error_msg