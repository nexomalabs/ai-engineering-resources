# Applied AI Engineering, Volume II, Chapter 18
# Section 18.9, Prompt Library APIs
# Copied from the book by scripts/export_listings.py. Report errors as errata.

class PromptLibraryAPI:
    """
    Minimal API contract for a prompt library.
    Implementations may use local files, databases, or remote services.
    """

    def get(self, prompt_id: str, version: str = "latest") -> "Prompt":
        """Retrieve a prompt by ID and optional version."""
        raise NotImplementedError

    def search(self, query: str = None, tags: list[str] = None,
               task_type: str = None) -> list[dict]:
        """Search the catalog and return matching prompt metadata."""
        raise NotImplementedError

    def list_versions(self, prompt_id: str) -> list[str]:
        """Return all available versions for a given prompt ID."""
        raise NotImplementedError

    def register(self, prompt: "Prompt", owner: str,
                 tags: list[str] = None) -> str:
        """Add a new prompt to the library."""
        raise NotImplementedError

    def update(self, prompt_id: str, new_prompt: "Prompt",
               change_description: str) -> str:
        """Update an existing prompt, creating a new version."""
        raise NotImplementedError

    def deprecate(self, prompt_id: str, version: str,
                  sunset_date: str, deprecated_by: str = None) -> None:
        """Mark a prompt version as deprecated."""
        raise NotImplementedError
