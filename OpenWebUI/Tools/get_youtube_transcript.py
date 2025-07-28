"""
title: Youtube Transcript Provider
author: theblackcat98
author_url: https://github.com/theblackcat98
git_url: https://github.com/Theblackcat98/Awesome-AI-Python-Scripts
description: A tool that returns the full transcript of a YouTube video with enhanced error handling and configuration.
requirements: langchain-yt-dlp
version: 0.2.0
license: MIT
"""

import unittest
import re
from typing import Any, Callable, Coroutine

# Note: The original code had a mix of langchain_yt_dlp and langchain_community.
# YoutubeLoader is in langchain_community, so we will stick with that.
from langchain_community.document_loaders import YoutubeLoader
from pydantic import BaseModel, Field


class EventEmitter:
    """A helper class to emit status updates."""

    def __init__(self, event_emitter: Callable[[dict], Coroutine[Any, Any, None]] = None):
        if event_emitter:
            self.event_emitter = event_emitter

    async def emit(self, status: str, description: str, done: bool = False):
        if hasattr(self, "event_emitter"):
            await self.event_emitter(
                {
                    "type": "status",
                    "data": {
                        "status": status,
                        "description": description,
                        "done": done,
                    },
                }
            )

    async def progress(self, description: str):
        await self.emit("in_progress", description)

    async def error(self, description: str):
        await self.emit("error", description, True)

    async def success(self, description: str):
        await self.emit("success", description, True)


class Tools:
    # This specific nested class "Valves" is what Open WebUI looks for to create UI settings.
    class Valves(BaseModel):
        TRANSCRIPT_LANGUAGE: str = Field(
            default="en",
            title="Transcript Languages",
            description="Comma-separated list of languages for the transcript, from highest to lowest priority (e.g., 'en,es').",
        )
        TRANSCRIPT_TRANSLATE_TO: str = Field(
            default="en",
            title="Translate To Language",
            description="The language to translate the transcript to if the desired language is not available.",
        )
        ADD_VIDEO_INFO: bool = Field(
            default=True,
            title="Add Video Info",
            description="If True, prepends the video title and author to the transcript.",
        )
        APPEND_SOURCE_CITATION: bool = Field(
            default=True,
            title="Append Source Citation",
            description="If True, appends the source YouTube URL to the end of the result.",
        )
        FAIL_ON_NO_TRANSCRIPT: bool = Field(
            default=True,
            title="Fail if No Transcript Found",
            description="If True, the tool returns an error if a transcript cannot be found. If False, it returns available video info.",
        )

    def __init__(self):
        # The __init__ method should be kept simple, as valves are passed per-call.
        pass

    async def get_youtube_transcript(
        self,
        url: str,
        __event_emitter__: Callable[[dict], Coroutine[Any, Any, None]] = None,
        __user__: dict | None = None,
    ) -> str:
        """
        Provides the transcript of a YouTube video with configurable options.
        Only use if the user supplies a valid YouTube URL.
        Examples: https://www.youtube.com/watch?v=H-JV9jGkG_g, https://youtu.be/H-JV9jGkG_g

        :param url: The URL of the YouTube video.
        :return: The video transcript and details, or a descriptive error message.
        """
        emitter = EventEmitter(__event_emitter__)
        
        # Correctly load and validate valves from the user object.
        if __user__ and "valves" in __user__:
            # If user provides valves, load them into the model.
            # This validates, applies defaults, and ensures correct types.
            valves = self.Valves.model_validate(__user__["valves"])
        else:
            # Otherwise, use the default valves.
            valves = self.Valves()

        try:
            await emitter.progress(f"Validating URL: {url}")
            youtube_regex = r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com|youtu\.be)\/(?:watch\?v=)?([\w-]{11})"
            if not url or not isinstance(url, str) or not re.match(youtube_regex, url):
                raise ValueError("Invalid or malformed YouTube URL provided. Please provide a valid URL (e.g., https://www.youtube.com/watch?v=...).")

            await emitter.progress("Fetching video transcript and metadata...")
            languages = [lang.strip() for lang in valves.TRANSCRIPT_LANGUAGE.split(",")]

            loader = YoutubeLoader.from_youtube_url(
                youtube_url=url,
                add_video_info=valves.ADD_VIDEO_INFO,
                language=languages,
                translation=valves.TRANSCRIPT_TRANSLATE_TO,
            )
            
            docs = await loader.aload()

            if not docs:
                raise ConnectionError("Failed to retrieve video data. The video may be private, deleted, age-restricted, or the URL is incorrect.")

            transcript_content = "\n".join([doc.page_content for doc in docs if doc.page_content])
            
            if not transcript_content and valves.FAIL_ON_NO_TRANSCRIPT:
                raise ValueError(f"No transcript found for the specified languages ('{valves.TRANSCRIPT_LANGUAGE}'). Check if the video has captions on YouTube.")

            # Prepare output
            result_parts = []
            title = ""
            if valves.ADD_VIDEO_INFO:
                metadata = docs[0].metadata
                title = metadata.get("title", "Unknown Title")
                author = metadata.get("author", "Unknown Author")
                result_parts.append(f"{title}\nby {author}\n")
                await emitter.progress(f"Found video: '{title}' by {author}")

            if transcript_content:
                result_parts.append(transcript_content)
            elif valves.ADD_VIDEO_INFO:
                result_parts.append("[No transcript was found or retrieved.]")
            
            if valves.APPEND_SOURCE_CITATION:
                result_parts.append(f"\n\nSource URL: {url}")

            final_result = "\n".join(result_parts).strip()
            await emitter.success(f"Successfully retrieved content for '{title or url}'.")
            return final_result

        except Exception as e:
            error_message = f"Error: {type(e).__name__} - {e}"
            await emitter.error(error_message)
            return error_message


class YoutubeTranscriptProviderTest(unittest.IsolatedAsyncioTestCase):
    
    async def test_get_valid_transcript_with_defaults(self):
        url = "https://www.youtube.com/watch?v=H-JV9jGkG_g"
        tool = Tools()
        response = await tool.get_youtube_transcript(url)
        
        self.assertIn("Open WebUI", response)
        self.assertIn("Source URL", response)
        self.assertTrue(len(response) > 100, "Transcript seems too short.")

    async def test_invalid_and_bad_urls(self):
        tool = Tools()
        
        response_invalid = await tool.get_youtube_transcript("https://www.example.com")
        self.assertIn("Invalid or malformed YouTube URL", response_invalid)

        response_missing = await tool.get_youtube_transcript("https://www.youtube.com/watch?v=nonexistent11")
        self.assertIn("Error: ConnectionError", response_missing)

    async def test_no_transcript_fail_valve(self):
        url = "https://www.youtube.com/watch?v=34Na4j8AVgA" # Music video, no transcript
        tool = Tools()
        user_settings = {"valves": {"FAIL_ON_NO_TRANSCRIPT": True}}
        response = await tool.get_youtube_transcript(url, __user__=user_settings)
        self.assertIn("Error: ValueError - No transcript found", response)

    async def test_no_transcript_pass_valve(self):
        url = "https://www.youtube.com/watch?v=34Na4j8AVgA"
        tool = Tools()
        user_settings = {"valves": {"FAIL_ON_NO_TRANSCRIPT": False}}
        response = await tool.get_youtube_transcript(url, __user__=user_settings)
        self.assertIn("Official Video", response)
        self.assertIn("[No transcript was found or retrieved.]", response)
        self.assertNotIn("Error:", response)

    async def test_custom_valves_no_info_or_citation(self):
        url = "https://www.youtube.com/watch?v=H-JV9jGkG_g"
        tool = Tools()
        user_settings = {
            "valves": {
                "ADD_VIDEO_INFO": False,
                "APPEND_SOURCE_CITATION": False
            }
        }
        response = await tool.get_youtube_transcript(url, __user__=user_settings)
        self.assertNotIn("Open WebUI", response)
        self.assertNotIn("Source URL", response)
        self.assertTrue(len(response) > 50)


if __name__ == "__main__":
    unittest.main()