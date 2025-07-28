"""
title: Youtube Transcript Provider
author: theblackcat98
author_url: https://github.com/theblackcat98
git_url: https://github.com/Theblackcat98/Awesome-AI-Python-Scripts
description: A tool that returns the full transcript of a YouTube video with enhanced error handling and configuration.
requirements: langchain-yt-dlp
version: 0.1.0
license: MIT
"""

import unittest
from typing import Any, Callable, Coroutine

from langchain_community.document_loaders import YoutubeLoader
from pydantic import BaseModel, Field


class EventEmitter:
    """A helper class to emit status updates."""

    def __init__(self, event_emitter: Callable[[dict], Coroutine[Any, Any, None]] = None):
        self.event_emitter = event_emitter

    async def emit(self, status: str, description: str, done: bool = False):
        if self.event_emitter:
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
    class UserValves(BaseModel):
        TRANSCRIPT_LANGUAGE: str = Field(
            default="en",
            description="A comma-separated list of languages for the transcript, from highest to lowest priority (e.g., 'en,es').",
        )
        TRANSCRIPT_TRANSLATE_TO: str = Field(
            default="en",
            description="The language to translate the transcript to if the desired language is not available.",
        )
        ADD_VIDEO_INFO: bool = Field(
            default=True,
            description="If True, prepends the video title and author to the transcript.",
        )
        APPEND_SOURCE_CITATION: bool = Field(
            default=True,
            description="If True, appends the source YouTube URL to the end of the result.",
        )
        FAIL_ON_NO_TRANSCRIPT: bool = Field(
            default=True,
            description="If True, the tool will return an error if a transcript cannot be found. If False, it will return available video info.",
        )

    def __init__(self):
        # Valves can be initialized here if needed, but are now primarily user-driven.
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
        Examples: https://www.youtube.com/watch?v=dQw4w9WgXcQ, https://youtu.be/H-JV9jGkG_g

        :param url: The URL of the YouTube video.
        :return: The video transcript and details, or a descriptive error message.
        """
        emitter = EventEmitter(__event_emitter__)

        # Fix for mutable default argument
        if __user__ is None:
            __user__ = {}
        if "valves" not in __user__:
            user_valves = self.UserValves()
        else:
            # Ensure user_valves is a Pydantic model for validation and default values
            user_valves = self.UserValves.model_validate(__user__["valves"])


        try:
            await emitter.progress(f"Validating URL: {url}")
            if not url or not isinstance(url, str) or not ("youtube.com/" in url or "youtu.be/" in url):
                raise ValueError(f"Invalid or missing YouTube URL provided.")

            await emitter.progress("Fetching video transcript and metadata...")
            languages = [lang.strip() for lang in user_valves.TRANSCRIPT_LANGUAGE.split(",")]

            loader = YoutubeLoader.from_youtube_url(
                url,
                add_video_info=user_valves.ADD_VIDEO_INFO,
                language=languages,
                translation=user_valves.TRANSCRIPT_TRANSLATE_TO,
            )
            
            docs = await loader.aload()

            if not docs:
                # This can happen if the video is private, deleted, or otherwise inaccessible.
                raise ConnectionError("Failed to retrieve video data. The video may be private, deleted, or the URL is incorrect.")

            transcript_content = "\n".join([doc.page_content for doc in docs if doc.page_content])
            
            if not transcript_content and user_valves.FAIL_ON_NO_TRANSCRIPT:
                raise ValueError(f"No transcript found for the specified languages ({user_valves.TRANSCRIPT_LANGUAGE}). Try a different language or check the video's YouTube page for available captions.")

            # Prepare output
            result_parts = []
            title = ""
            author = ""

            if user_valves.ADD_VIDEO_INFO:
                metadata = docs[0].metadata
                title = metadata.get("title", "Unknown Title")
                author = metadata.get("author", "Unknown Author")
                result_parts.append(f"{title}\nby {author}\n")
                await emitter.progress(f"Found video: '{title}' by {author}")

            if transcript_content:
                result_parts.append(transcript_content)
            elif user_valves.ADD_VIDEO_INFO:
                result_parts.append("[No transcript was found or retrieved.]")
            
            if user_valves.APPEND_SOURCE_CITATION:
                result_parts.append(f"\n\nSource URL: {url}")

            final_result = "\n".join(result_parts).strip()
            await emitter.success("Successfully retrieved YouTube video content.")
            return final_result

        except Exception as e:
            error_message = f"An error occurred: {type(e).__name__} - {e}"
            await emitter.error(error_message)
            return error_message


class YoutubeTranscriptProviderTest(unittest.IsolatedAsyncioTestCase):
    
    async def test_get_valid_transcript(self):
        # A short, stable video.
        url = "https://www.youtube.com/watch?v=H-JV9jGkG_g"
        tool = Tools()
        response = await tool.get_youtube_transcript(url)
        
        self.assertIn("Open WebUI", response) # Check for title
        self.assertIn("Source URL", response) # Check for citation
        # Check for reasonable length instead of exact match
        self.assertTrue(len(response) > 100, "Transcript seems too short.")

    async def test_invalid_and_bad_urls(self):
        tool = Tools()
        
        # Completely invalid URL
        invalid_url = "https://www.example.com"
        response_invalid = await tool.get_youtube_transcript(invalid_url)
        self.assertIn("Invalid or missing YouTube URL", response_invalid)

        # Non-existent video
        missing_video_url = "https://www.youtube.com/watch?v=nonexistentvideo"
        response_missing = await tool.get_youtube_transcript(missing_video_url)
        self.assertIn("ConnectionError", response_missing)
        self.assertIn("private, deleted, or the URL is incorrect", response_missing)

    async def test_no_transcript_found_fails(self):
        # A video known to have no English transcript (e.g., a music video)
        url = "https://www.youtube.com/watch?v=34Na4j8AVgA"
        tool = Tools()
        # Default valve should fail
        response = await tool.get_youtube_transcript(url)
        self.assertIn("No transcript found", response)

    async def test_no_transcript_found_succeeds_with_valve(self):
        # Same video, but with the valve set to not fail
        url = "https://www.youtube.com/watch?v=34Na4j8AVgA"
        tool = Tools()
        user_settings = {
            "valves": {
                "FAIL_ON_NO_TRANSCRIPT": False
            }
        }
        response = await tool.get_youtube_transcript(url, __user__=user_settings)
        self.assertIn("Official Video", response) # Should get title
        self.assertIn("[No transcript was found or retrieved.]", response)
        self.assertNotIn("Error", response)

    async def test_valves_functionality(self):
        url = "https://www.youtube.com/watch?v=H-JV9jGkG_g"
        tool = Tools()
        user_settings = {
            "valves": {
                "ADD_VIDEO_INFO": False,
                "APPEND_SOURCE_CITATION": False
            }
        }
        response = await tool.get_youtube_transcript(url, __user__=user_settings)
        # Should not contain title or citation
        self.assertNotIn("Open WebUI", response)
        self.assertNotIn("Source URL", response)
        self.assertTrue(len(response) > 50)


if __name__ == "__main__":
    unittest.main()