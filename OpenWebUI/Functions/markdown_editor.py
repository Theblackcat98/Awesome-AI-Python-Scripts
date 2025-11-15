"""
Title: Canvas Markdown Editor
Author: Your Name/AI
Version: 1.0.0
Required OpenWebUI Version: 0.5.0
Description: An interactive Markdown editor pipe for OpenWebUI.
"""

import os
import re
import uuid
import html
import traceback
import json
from typing import Optional, List, Dict, Any, Callable, Awaitable
import sys # Added for flushing print

from pydantic import BaseModel, Field
# Assuming UPLOAD_DIR and File handling utilities are accessible
# If not, these need to be defined or imported appropriately.
# For standalone, we might need to mock or simplify these.
try:
    from open_webui.config import UPLOAD_DIR
    from open_webui.models.files import Files, FileForm
except ImportError:
    print("OpenWebUI specific imports failed. Using placeholder UPLOAD_DIR.")
    UPLOAD_DIR = "uploads" # Placeholder
    # Mock FileForm and Files for standalone testing if needed
    class FileForm(BaseModel):
        id: str
        filename: str
        meta: Dict[str, Any]

    class Files:
        @staticmethod
        def insert_new_file(user_id, file_form: FileForm) -> FileForm:
            print(f"Mock insert_new_file: {user_id}, {file_form.filename}")
            return file_form


class MarkdownMiddlewareHTMLGenerator:
    @staticmethod
    def generate_style() -> str:
        return """
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #1e1e1e;
            color: #ffffff;
            display: flex;
            flex-direction: column;
            height: 100vh;
            overflow: hidden; /* Prevent body scroll, manage scrolling in panes */
        }
        .header {
            height: 40px;
            background-color: #2d2d2d;
            display: flex;
            align-items: center;
            justify-content: space-between; /* Push toolbar to the right */
            padding: 0 10px;
            flex-shrink: 0; /* Header should not shrink */
        }
        .header-title {
            font-size: 1.1em;
        }
        .toolbar button {
            background-color: #4a4a4a;
            color: white;
            border: none;
            padding: 5px 10px;
            margin: 0 2px;
            cursor: pointer;
            border-radius: 3px;
        }
        .toolbar button:hover {
            background-color: #5a5a5a;
        }
        .container {
            display: flex;
            flex-grow: 1; /* Container takes remaining space */
            overflow: hidden; /* Prevent container from overflowing body */
        }
        .editor-pane, .preview-pane {
            flex: 1;
            padding: 10px;
            overflow-y: auto; /* Allow individual scrolling */
            height: calc(100vh - 40px - 20px); /* Full height minus header and padding */
            box-sizing: border-box;
        }
        .editor-pane {
            border-right: 1px solid #444;
        }
        #markdown-editor {
            width: 100%;
            height: 100%; /* Editor takes full height of its pane */
            background-color: #252526;
            color: #cccccc;
            border: none;
            padding: 8px;
            font-family: 'Courier New', Courier, monospace;
            font-size: 14px;
            box-sizing: border-box;
            resize: none; /* Disable textarea native resize */
        }
        #markdown-preview {
            background-color: #1e1e1e;
            color: #cccccc;
            padding: 8px;
            word-wrap: break-word;
        }
        /* Basic Markdown styling for preview */
        #markdown-preview h1, #markdown-preview h2, #markdown-preview h3 {
            border-bottom: 1px solid #444;
            padding-bottom: 0.3em;
        }
        #markdown-preview code {
            background-color: #2d2d2d;
            padding: 0.2em 0.4em;
            border-radius: 3px;
        }
        #markdown-preview pre {
            background-color: #2d2d2d;
            padding: 10px;
            border-radius: 5px;
            overflow-x: auto;
        }
        #markdown-preview pre code {
            padding: 0;
            background-color: transparent;
        }
        #markdown-preview blockquote {
            border-left: 4px solid #555;
            padding-left: 1em;
            color: #aaa;
            margin-left: 0;
        }
        #markdown-preview table {
            border-collapse: collapse;
            width: auto;
            margin-bottom: 1em;
        }
        #markdown-preview th, #markdown-preview td {
            border: 1px solid #444;
            padding: 0.5em;
        }
        #markdown-preview th {
            background-color: #333;
        }
        .hidden { display: none; }
        .view-toggle-buttons button { margin-left: 10px; }
        """

    @staticmethod
    def generate_script(initial_markdown: str) -> str:
        # Escape the initial markdown for direct embedding in a JS string
        escaped_initial_markdown = json.dumps(initial_markdown)

        return f"""
        // Include Marked.js library from CDN
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/marked/marked.min.js';
        document.head.appendChild(script);

        script.onload = () => {{
            const editor = document.getElementById('markdown-editor');
            const preview = document.getElementById('markdown-preview');
            const documentId = 'current_markdown_document'; // For localStorage

            // Toolbar buttons
            const boldButton = document.getElementById('bold-btn');
            const italicButton = document.getElementById('italic-btn');
            const codeButton = document.getElementById('code-btn');
            const linkButton = document.getElementById('link-btn');
            const listButton = document.getElementById('list-btn');
            
            const editorPane = document.querySelector('.editor-pane');
            const previewPane = document.querySelector('.preview-pane');
            const toggleEditorButton = document.getElementById('toggle-editor-btn');
            const togglePreviewButton = document.getElementById('toggle-preview-btn');
            const toggleSplitButton = document.getElementById('toggle-split-btn');


            function updatePreview() {{
                const markdownText = editor.value;
                if (window.marked) {{
                    preview.innerHTML = window.marked.parse(markdownText);
                }}
                localStorage.setItem(documentId, markdownText);
            }}

            function insertText(prefix, suffix = '') {{
                const start = editor.selectionStart;
                const end = editor.selectionEnd;
                const text = editor.value;
                const selectedText = text.substring(start, end);
                const newText = prefix + selectedText + suffix;
                
                editor.value = text.substring(0, start) + newText + text.substring(end);
                
                editor.focus();
                if (selectedText) {{
                     editor.selectionStart = start + prefix.length;
                     editor.selectionEnd = start + prefix.length + selectedText.length;
                }} else {{
                    editor.selectionStart = start + prefix.length;
                    editor.selectionEnd = start + prefix.length;
                }}
                updatePreview();
            }}

            if (boldButton) boldButton.addEventListener('click', () => insertText('**', '**'));
            if (italicButton) italicButton.addEventListener('click', () => insertText('*', '*'));
            if (codeButton) codeButton.addEventListener('click', () => insertText('`', '`'));
            if (linkButton) linkButton.addEventListener('click', () => {{
                const url = prompt("Enter URL:", "http://");
                if (url) {{
                    insertText('[', `](${'{url}'})`);
                }}
            }});
            if (listButton) listButton.addEventListener('click', () => insertText('- '));

            if (toggleEditorButton) toggleEditorButton.addEventListener('click', () => {{
                editorPane.classList.remove('hidden');
                editorPane.style.flex = '1';
                previewPane.classList.add('hidden');
                previewPane.style.flex = '0';
            }});
            if (togglePreviewButton) togglePreviewButton.addEventListener('click', () => {{
                previewPane.classList.remove('hidden');
                previewPane.style.flex = '1';
                editorPane.classList.add('hidden');
                editorPane.style.flex = '0';
            }});
            if (toggleSplitButton) toggleSplitButton.addEventListener('click', () => {{
                editorPane.classList.remove('hidden');
                previewPane.classList.remove('hidden');
                editorPane.style.flex = '1';
                previewPane.style.flex = '1';
            }});
            
            // Debounce updatePreview
            let debounceTimer;
            editor.addEventListener('input', () => {{
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(updatePreview, 250);
            }});

            // Load saved content or initial content
            const savedMarkdown = localStorage.getItem(documentId);
            editor.value = savedMarkdown !== null ? savedMarkdown : {escaped_initial_markdown};
            
            // Initial preview
            // Wait a bit for marked to be surely loaded if script.onload is tricky
            setTimeout(updatePreview, 100); 
        }};
        """

    @classmethod
    def create_middleware_html(cls, markdown_content: str) -> str:
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Interactive Markdown Editor</title>
            <style>
                {cls.generate_style()}
            </style>
        </head>
        <body>
            <div class="header">
                <span class="header-title">Markdown Editor</span>
                <div class="toolbar">
                    <button id="bold-btn" title="Bold">B</button>
                    <button id="italic-btn" title="Italic">I</button>
                    <button id="code-btn" title="Code">{"{ }"}</button>
                    <button id="link-btn" title="Link">Link</button>
                    <button id="list-btn" title="List">- List</button>
                </div>
                <div class="view-toggle-buttons">
                    <button id="toggle-editor-btn" title="Editor Only">Editor</button>
                    <button id="toggle-preview-btn" title="Preview Only">Preview</button>
                    <button id="toggle-split-btn" title="Split View">Split</button>
                </div>
            </div>
            <div class="container">
                <div class="editor-pane">
                    <textarea id="markdown-editor"></textarea>
                </div>
                <div class="preview-pane">
                    <div id="markdown-preview"></div>
                </div>
            </div>
            <script>
                {cls.generate_script(markdown_content)}
            </script>
        </body>
        </html>
        """

class Pipe:
    class Valves(BaseModel):
        priority: int = Field(default=0, description="Priority for the filter.")
        enabled: bool = Field(default=True, description="Enable/disable the Markdown editor filter.")
        # Could add more valves later, e.g., default markdown template, extract pattern

    class UserValves(BaseModel): # User-specific settings if needed later
        show_status_notifications: bool = Field(default=True, description="Show status notifications for processing.")

    def __init__(self):
        self.valves = self.Valves()
        # Ensure UPLOAD_DIR and viz_dir are correctly set up
        self.viz_dir = os.path.join("markdown_editor", "sessions") # More specific path
        if not os.path.exists(os.path.join(UPLOAD_DIR, self.viz_dir)):
            os.makedirs(os.path.join(UPLOAD_DIR, self.viz_dir), exist_ok=True)
        
        # This would store markdown content per chat_id if we want persistence beyond one message
        # For V1, each message might just generate a new editor instance.
        self.chat_documents: Dict[str, str] = {}


    def ensure_chat_directory(self, chat_id: str) -> str:
        # Path will be uploads/markdown_editor/sessions/<chat_id>/html
        # The "html" part is where the middleware HTML files themselves will be stored.
        # The actual markdown content isn't directly saved as a separate .md file in this V1.
        chat_specific_html_dir = os.path.join(UPLOAD_DIR, self.viz_dir, chat_id, "html")
        os.makedirs(chat_specific_html_dir, exist_ok=True)
        return chat_specific_html_dir

    def write_content_to_file(self, content: str, user_id: str, chat_id: str) -> str:
        """Writes the middleware HTML content to a file and returns its file ID."""
        chat_dir = self.ensure_chat_directory(chat_id) # This is now .../<chat_id>/html
        filename = f"md_editor_{uuid.uuid4()}.html"
        file_path = os.path.join(chat_dir, filename)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        # Relative path for OpenWebUI to find the file from its UPLOAD_DIR perspective
        # Example: markdown_editor/sessions/<chat_id>/html/md_editor_uuid.html
        relative_path = os.path.join(self.viz_dir, chat_id, "html", filename)
        
        file_form = FileForm(
            id=str(uuid.uuid4()), # This ID is for the database record
            filename=relative_path, # This is the path OpenWebUI will use
            meta={
                "name": filename, # Display name
                "content_type": "text/html",
                "size": len(content.encode('utf-8')),
                "path": file_path, # Absolute path on server
            },
        )
        # This Files.insert_new_file is a mock if OpenWebUI components are not available
        db_file_record = Files.insert_new_file(user_id, file_form)
        return db_file_record.id # Return the ID of the database record for the file

    def extract_markdown(self, content: str) -> Optional[str]:
        """
        Extracts Markdown content.
        For V1, let's assume the LLM might wrap it in ```markdown ... ```
        or we can have a setting to treat the whole message as markdown if no pattern found.
        """
        # Regex to find ```markdown ... ``` or ```md ... ``` blocks
        patterns = [
            r"```markdown\s*([\s\S]*?)\s*```",
            r"```md\s*([\s\S]*?)\s*```"
        ]
        for pattern in patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                return match.group(1).strip()
        
        # If no specific block found, maybe treat the whole content if it looks like Markdown?
        # For now, let's be explicit. If no block, no Markdown.
        # A fallback could be: if "[[MARKDOWN_DOCUMENT]]" in content, take everything after.
        return None

    async def inlet(
        self,
        body: Dict,
        __event_emitter__: Optional[Callable[[Any], Awaitable[None]]] = None,
        __user__: Optional[Dict] = None,
    ) -> Dict:
        # For V1, inlet might not do much.
        # For future, if editor can send data back to influence LLM.
        return body

    async def outlet(
        self,
        body: Dict,
        __event_emitter__: Optional[Callable[[Any], Awaitable[None]]] = None,
        __user__: Optional[Dict] = None,
    ) -> Dict:
        print("MarkdownEditorFilter DEBUG: outlet method entered.", flush=True) # DEBUG Entry Point

        if not self.valves.enabled:
            print("MarkdownEditorFilter DEBUG: Pipe is not enabled, exiting outlet.", flush=True) # DEBUG
            return body

        user_id = __user__.get("id") if __user__ else None
        chat_id = body.get("chat_id")

        if not (user_id and chat_id):
            print("MarkdownEditorFilter DEBUG: User ID or Chat ID is missing.", flush=True) # DEBUG
            return body
            
        if "messages" in body and body["messages"]:
            last_message_obj = body["messages"][-1]
            llm_content = last_message_obj.get("content", "")
            print(f"MarkdownEditorFilter DEBUG: llm_content (first 200): {llm_content[:200]}", flush=True) # DEBUG

            try:
                extracted_markdown = self.extract_markdown(llm_content)
                print(f"MarkdownEditorFilter DEBUG: Extracted Markdown: {extracted_markdown[:200] if extracted_markdown else 'None'}", flush=True) # DEBUG

                if extracted_markdown is not None:
                    self.chat_documents[chat_id] = extracted_markdown 
                    
                    print(f"MarkdownEditorFilter: Extracted Markdown for chat {chat_id[:5]}...: {len(extracted_markdown)} chars", flush=True) # DEBUG

                    middleware_html_content = MarkdownMiddlewareHTMLGenerator.create_middleware_html(
                        markdown_content=extracted_markdown
                    )
                    print(f"MarkdownEditorFilter DEBUG: Generated HTML (first 500 chars): {middleware_html_content[:500]}", flush=True) # DEBUG
                    
                    file_db_id = self.write_content_to_file(
                        middleware_html_content,
                        user_id,
                        chat_id
                    )
                    print(f"MarkdownEditorFilter DEBUG: Obtained File DB ID: {file_db_id}", flush=True) # DEBUG

                    last_message_obj["content"] += f"\\n\\n{{{{HTML_FILE_ID_{file_db_id}}}}}"
                    print(f"MarkdownEditorFilter DEBUG: Final message content (last 200): {last_message_obj['content'][-200:]}", flush=True) # DEBUG
                    
                    if __event_emitter__ and __user__ and __user__.get("valves", {}).get("show_status_notifications", True):
                        await __event_emitter__({
                            "type": "status",
                            "data": {"description": "Markdown document editor ready.", "done": True},
                        })
                else:
                    print("MarkdownEditorFilter DEBUG: No markdown found in the message.", flush=True) # DEBUG
                    pass

            except Exception as e:
                error_msg = f"Error processing Markdown content: {str(e)}\\n{traceback.format_exc()}"
                print(f"MarkdownEditorFilter DEBUG: Exception in outlet: {error_msg}", flush=True) # DEBUG
                last_message_obj["content"] += f"\\n\\nError creating Markdown editor: {html.escape(str(e))}"
                if __event_emitter__ and __user__ and __user__.get("valves", {}).get("show_status_notifications", True):
                    await __event_emitter__({
                        "type": "status",
                        "data": {"description": f"Error creating editor: {html.escape(str(e))}", "done": True},
                    })
        else:
            print("MarkdownEditorFilter DEBUG: No messages found in body or body is empty.", flush=True) # DEBUG
        return body

# Example usage for standalone testing (won't fully work without OpenWebUI context)
async def run_test():
    filter_instance = Pipe()
    
    # Mock user and body
    mock_user = {"id": "test_user_123", "valves": {"show_status_notifications": True}}
    mock_chat_id = "chat_abc_789"

    # Ensure the base UPLOAD_DIR exists for mock file operations
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)

    llm_message_with_markdown = """
Hello! Here's the document draft:

```markdown
# My Awesome Document

This is the first section.

## Subsection 1.1
- Item 1
- Item 2

Here's some **bold** and *italic* text.
And a [link](https://example.com).
```

What do you think?
    """
    
    test_body = {
        "chat_id": mock_chat_id,
        "messages": [
            {"role": "assistant", "content": llm_message_with_markdown}
        ]
    }

    print(f"Initial body: {test_body}")
    
    async def mock_emitter(event):
        print(f"MOCK EMITTER Event: {event['type']} - {event['data']}")

    updated_body = await filter_instance.outlet(test_body, __event_emitter__=mock_emitter, __user__=mock_user)
    
    print(f"Updated body: {json.dumps(updated_body, indent=2)}")
    if "{{HTML_FILE_ID_" in updated_body["messages"][-1]["content"]:
        print("\\n--- Test successful: HTML_FILE_ID found ---")
        # You can find the generated HTML file in uploads/markdown_editor/sessions/chat_abc_789/html/
    else:
        print("\\n--- Test potentially failed: HTML_FILE_ID NOT found ---")

if __name__ == "__main__":
    # This part is for basic testing of the class structure.
    # To fully test, it needs to be run within the OpenWebUI environment.
    import asyncio
    asyncio.run(run_test()) 