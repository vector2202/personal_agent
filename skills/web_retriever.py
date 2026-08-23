import urllib.request
import urllib.error
import re
from typing import Type, Dict, Any, Optional
from pydantic import BaseModel, Field
from skills.base import BaseSkill

class WebRetrieverInput(BaseModel):
    url: str = Field(..., description="The HTTP or HTTPS URL to retrieve content and documentation from.")
    max_length: int = Field(default=3000, ge=500, le=10000, description="Max characters of parsed text to return.")

class WebDocRetriever(BaseSkill):
    """
    Retrieves web pages and documentation to access live, updated information.
    Strips raw HTML tags to return clean, readable text.
    """

    @property
    def name(self) -> str:
        return "web_doc_retriever"

    @property
    def description(self) -> str:
        return "Fetches live web content and official documentation from URLs, stripping HTML markup."

    @property
    def input_schema(self) -> Type[BaseModel]:
        return WebRetrieverInput

    def _strip_html(self, html_text: str) -> str:
        # Remove scripts and styles
        cleaned = re.sub(r'<script.*?</script>', '', html_text, flags=re.DOTALL | re.IGNORECASE)
        cleaned = re.sub(r'<style.*?</style>', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        # Strip all HTML tags
        cleaned = re.sub(r'<[^>]+>', ' ', cleaned)
        # Collapse multiple whitespaces
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        data = self.input_schema(**params)

        req = urllib.request.Request(
            data.url,
            headers={"User-Agent": "PersonalAgent-DocRetriever/1.0 (Python WebClient)"}
        )

        try:
            with urllib.request.urlopen(req, timeout=12) as response:
                raw_bytes = response.read()
                raw_html = raw_bytes.decode("utf-8", errors="replace")

            text_content = self._strip_html(raw_html)
            truncated = len(text_content) > data.max_length

            return {
                "success": True,
                "url": data.url,
                "length": len(text_content),
                "is_truncated": truncated,
                "content": text_content[:data.max_length]
            }
        except urllib.error.HTTPError as e:
            return {"success": False, "error": f"HTTP {e.code}: {e.reason}"}
        except Exception as e:
            return {"success": False, "error": f"Failed to retrieve web document: {str(e)}"}
