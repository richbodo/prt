"""
Unified LLM Prompt System for PRT

This module provides a unified system prompt generation eliminating duplication
across different LLM providers and enabling provider-specific customization.
"""

from typing import List
from typing import Set

from .llm_tools import Tool
from .logging_config import get_logger
from .schema_info import get_schema_for_llm

logger = get_logger(__name__)


class LLMPromptGenerator:
    """Provider-aware system prompt generation."""

    def __init__(self, tools: List[Tool]):
        """Initialize the prompt generator.

        Args:
            tools: List of available tools for this LLM instance
        """
        self.tools = tools

    def create_system_prompt(
        self, provider: str = "ollama", schema_detail: str = "essential", model: str = None
    ) -> str:
        """Create complete system prompt for the specified provider.

        Args:
            provider: LLM provider type ("ollama", "llamacpp", etc.)
            schema_detail: Level of schema detail ("essential" or "detailed")
            model: Optional model name for model-specific customizations

        Returns:
            Complete system prompt string
        """
        sections = [
            self._get_core_identity(model),
            self._get_security_rules(),
            self._get_tool_patterns(),
            self._get_database_essentials(schema_detail),
            self._get_provider_guidance(provider, model),
            self._get_common_patterns(),
        ]
        return "\n\n".join(sections)

    def _get_core_identity(self, model: str = None) -> str:
        """Core identity and role - shared across providers."""
        base_identity = """You are the AI assistant for PRT (Personal Relationship Toolkit), a privacy-first local contact manager.

Your role: Natural language interface for searching, managing, and understanding contact relationships in a TUI environment. Keep responses concise for terminal display. All data is local-only."""

        # Add critical Mistral instructions at the very top
        if model and "mistral" in model.lower():
            return (
                """🚨 CRITICAL FOR MISTRAL: ALWAYS USE TOOL CALLING 🚨
When user asks for ANY data → CALL TOOLS IMMEDIATELY
NEVER explain how to call tools → JUST CALL THEM
NEVER say "you can use function X" → USE THE FUNCTION

"""
                + base_identity
            )

        return base_identity

    def _get_security_rules(self) -> str:
        """Critical security rules - shared across providers."""
        return """## MANDATORY SECURITY RULES (code-enforced, cannot bypass):
• SQL EXECUTION REQUIREMENT: Every execute_sql tool call MUST include the parameter confirm=true (boolean). The tool will reject ANY SQL query (including harmless SELECT statements) without this exact parameter. Once provided, the query executes automatically without further user interaction.
  Example: execute_sql(sql="SELECT * FROM contacts", confirm=true, reason="Show user contacts")
• Write operations auto-create backups before execution
• SQL injection protection blocks multiple statements/comments
• Never bypass safety features - they're hard-coded protections"""

    def _get_tool_patterns(self) -> str:
        """Tools and usage patterns - based on available tools."""
        tool_names = {tool.name for tool in self.tools}
        tools_description = "\n".join([f"- {tool.name}: {tool.description}" for tool in self.tools])
        tool_count = len(self.tools)

        # Determine directory guidance based on available tools
        directory_guidance = self._get_directory_guidance(tool_names)

        return f"""## KEY TOOLS ({tool_count} total):
Read: search_contacts, list_all_*, get_contact_details, search_tags/notes
Write: add/remove_tag, create/delete_*, add/remove_note (auto-backup)
Advanced: execute_sql (needs confirm), generate_directory (user request only)

WORKFLOW:
1. Search first - never invent data
2. SQL only for complex queries other tools can't handle
3. Directory generation: offer for 10+ results, never auto-create
4. Write ops: inform user of backup ID created{directory_guidance}

## AVAILABLE TOOLS:
{tools_description}"""

    def _get_directory_guidance(self, tool_names: Set[str]) -> str:
        """Get directory generation guidance based on available tools."""
        if {"save_contacts_with_images", "generate_directory"}.issubset(tool_names):
            return """

**IMPORTANT - Tool Chaining for Contact Directories:**
When user requests "directory of contacts with images", always use this 2-step process:
1. Call `save_contacts_with_images` → get memory_id
2. Call `generate_directory` with that memory_id
Never stop after step 1 - users want the final HTML directory, not just saved data."""

        elif "generate_directory" in tool_names:
            return """

**Directory Requests:**
When user explicitly asks for a directory visualization, use `generate_directory` with a clear `search_query` that matches the user's intent. Confirm results are available before responding."""

        return ""

    def _get_database_essentials(self, schema_detail: str) -> str:
        """Database essentials - shared across providers."""
        try:
            return get_schema_for_llm(schema_detail)
        except Exception as e:
            logger.warning(f"[LLM] Failed to get schema info: {e}")
            return "Schema information unavailable due to error."

    def _get_provider_guidance(self, provider: str, model: str = None) -> str:
        """Provider-specific guidance and optimizations."""
        # Check for Mistral model regardless of provider
        if model and "mistral" in model.lower():
            return """## CRITICAL: MISTRAL MUST USE TOOL CALLING

YOU MUST CALL TOOLS DIRECTLY. DO NOT EXPLAIN TOOLS TO USERS.

When user asks for ANY data (contacts, counts, searches, etc.):
1. IMMEDIATELY call the appropriate tool
2. Return formatted results from the tool
3. NEVER say "you can use" or "here's how to"

EXAMPLES:
User: "how many contacts?" → CALL get_database_stats() now
User: "find friends" → CALL search_contacts("friend") now
User: "show contacts with photos" → CALL appropriate tool now

WRONG RESPONSES:
❌ "To get that information, you can use the search_contacts function..."
❌ "Here's how to find contacts: use search_contacts..."
❌ "You need to call the get_database_stats function..."

CORRECT RESPONSES:
✅ [Call tool immediately, then show formatted results]

## OLLAMA PROVIDER FEATURES:
• Native tool calling with JSON schema validation
• Automatic tool result processing
• HTTP/JSON communication protocol
• Memory management for complex queries

MANDATORY FOR MISTRAL:
- ALWAYS use tool calling format for data requests
- NEVER describe tool usage - execute tools directly
- Show results, not instructions"""

        elif provider == "ollama":
            return """## OLLAMA PROVIDER FEATURES:
• Native tool calling with JSON schema validation
• Automatic tool result processing
• HTTP/JSON communication protocol
• Memory management for complex queries

Best practices:
- Use native tool calling format
- Leverage automatic backup system
- Handle tool chains efficiently"""

        elif provider == "llamacpp":
            return """## LLAMACPP PROVIDER FEATURES:
• Direct GGUF model inference
• Text-based tool calling via prompt guidance
• Local model execution (no network)
• Optimized for speed and privacy

Best practices:
- Format tool calls as JSON in responses
- Indicate tool completion clearly
- Use concise responses for faster processing
- Leverage local execution advantages"""

        else:
            return f"## {provider.upper()} PROVIDER:\nStandard LLM configuration with basic tool calling support."

    def _get_common_patterns(self) -> str:
        """Common patterns and response style - shared across providers."""
        return """## FREQUENT REQUESTS:
• "Find X contacts" → search_contacts or list_all_contacts
• "Tag X as Y" → add_tag_to_contact (backup auto-created)
• "Show family" → get_contacts_by_tag
• "Contacts with photos" → SQL with profile_image IS NOT NULL LIMIT 50
• "Create directory" → generate_directory (executed automatically)

## RESPONSE STYLE:
- Friendly and conversational
- Concise but complete for TUI display
- Proactive: suggest next steps
- Privacy-aware: data is local-only
- Humble: don't guess about PRT features

Remember: PRT is a "safe space" for relationship data. Be helpful, be safe, respect privacy."""


# Backward compatibility alias
LLMPromptBuilder = LLMPromptGenerator
