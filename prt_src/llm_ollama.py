"""
Ollama LLM Integration for PRT

This module provides integration with Ollama for running GPT-OSS-20B locally
with tool calling capabilities for PRT operations.
"""

import json
import requests
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from .api import PRTAPI


@dataclass
class Tool:
    """Represents a tool that can be called by the LLM."""
    name: str
    description: str
    parameters: Dict[str, Any]
    function: Callable


class OllamaLLM:
    """Ollama LLM client with tool calling support."""
    
    def __init__(self, api: PRTAPI, base_url: str = "http://localhost:11434/v1"):
        """Initialize Ollama LLM client."""
        self.api = api
        self.base_url = base_url
        self.model = "gpt-oss:20b"
        self.tools = self._create_tools()
        self.conversation_history = []
    
    def _create_tools(self) -> List[Tool]:
        """Create the available tools for the LLM."""
        return [
            Tool(
                name="search_contacts",
                description="Search for contacts by name, email, or other criteria",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search term to find contacts"
                        }
                    },
                    "required": ["query"]
                },
                function=self.api.search_contacts
            ),
            Tool(
                name="list_all_contacts",
                description="Get a list of all contacts in the database",
                parameters={
                    "type": "object",
                    "properties": {}
                },
                function=self.api.list_all_contacts
            ),
            Tool(
                name="get_contact_details",
                description="Get detailed information about a specific contact",
                parameters={
                    "type": "object",
                    "properties": {
                        "contact_id": {
                            "type": "integer",
                            "description": "ID of the contact to get details for"
                        }
                    },
                    "required": ["contact_id"]
                },
                function=self.api.get_contact_details
            ),
            Tool(
                name="search_tags",
                description="Search for tags by name",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search term to find tags"
                        }
                    },
                    "required": ["query"]
                },
                function=self.api.search_tags
            ),
            Tool(
                name="list_all_tags",
                description="Get a list of all tags in the database",
                parameters={
                    "type": "object",
                    "properties": {}
                },
                function=self.api.list_all_tags
            ),
            Tool(
                name="get_contacts_by_tag",
                description="Get all contacts that have a specific tag",
                parameters={
                    "type": "object",
                    "properties": {
                        "tag_name": {
                            "type": "string",
                            "description": "Name of the tag to search for"
                        }
                    },
                    "required": ["tag_name"]
                },
                function=self.api.get_contacts_by_tag
            ),
            Tool(
                name="search_notes",
                description="Search for notes by title or content",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search term to find notes"
                        }
                    },
                    "required": ["query"]
                },
                function=self.api.search_notes
            ),
            Tool(
                name="list_all_notes",
                description="Get a list of all notes in the database",
                parameters={
                    "type": "object",
                    "properties": {}
                },
                function=self.api.list_all_notes
            ),
            Tool(
                name="get_contacts_by_note",
                description="Get all contacts that have a specific note",
                parameters={
                    "type": "object",
                    "properties": {
                        "note_title": {
                            "type": "string",
                            "description": "Title of the note to search for"
                        }
                    },
                    "required": ["note_title"]
                },
                function=self.api.get_contacts_by_note
            ),
            Tool(
                name="add_tag_to_contact",
                description="Add a tag to a contact's relationship",
                parameters={
                    "type": "object",
                    "properties": {
                        "contact_id": {
                            "type": "integer",
                            "description": "ID of the contact"
                        },
                        "tag_name": {
                            "type": "string",
                            "description": "Name of the tag to add"
                        }
                    },
                    "required": ["contact_id", "tag_name"]
                },
                function=self.api.add_tag_to_contact
            ),
            Tool(
                name="add_note_to_contact",
                description="Add a note to a contact's relationship",
                parameters={
                    "type": "object",
                    "properties": {
                        "contact_id": {
                            "type": "integer",
                            "description": "ID of the contact"
                        },
                        "note_title": {
                            "type": "string",
                            "description": "Title of the note"
                        },
                        "note_content": {
                            "type": "string",
                            "description": "Content of the note"
                        }
                    },
                    "required": ["contact_id", "note_title", "note_content"]
                },
                function=self.api.add_note_to_contact
            ),
            Tool(
                name="create_tag",
                description="Create a new tag",
                parameters={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the tag to create"
                        }
                    },
                    "required": ["name"]
                },
                function=self.api.create_tag
            ),
            Tool(
                name="create_note",
                description="Create a new note",
                parameters={
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Title of the note"
                        },
                        "content": {
                            "type": "string",
                            "description": "Content of the note"
                        }
                    },
                    "required": ["title", "content"]
                },
                function=self.api.create_note
            ),
            Tool(
                name="get_database_stats",
                description="Get database statistics including contact and relationship counts",
                parameters={
                    "type": "object",
                    "properties": {}
                },
                function=self.api.get_database_stats
            )
        ]
    
    def _get_tool_by_name(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        for tool in self.tools:
            if tool.name == name:
                return tool
        return None
    
    def _call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool with the given arguments."""
        tool = self._get_tool_by_name(tool_name)
        if not tool:
            return {"error": f"Tool '{tool_name}' not found"}
        
        try:
            result = tool.function(**arguments)
            return result
        except Exception as e:
            return {"error": f"Error calling tool '{tool_name}': {str(e)}"}
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for the LLM."""
        tools_description = "\n".join([
            f"- {tool.name}: {tool.description}" for tool in self.tools
        ])
        
        return f"""You are an AI assistant for the Personal Relationship Toolkit (PRT). You help users manage their contacts, relationships, tags, and notes.

Available tools:
{tools_description}

You can use these tools to help users with their requests. When a user asks you to do something, use the appropriate tool(s) to accomplish the task.

Guidelines:
1. Always use tools to perform actions rather than making up information
2. Be helpful and conversational in your responses
3. When showing results, format them clearly and concisely
4. If you need to search for something, use the appropriate search tool first
5. You can combine multiple tool calls to complete complex tasks

Remember: You can only use the tools listed above. You cannot access the file system, run terminal commands, or modify database configuration directly."""
    
    def _format_tool_calls(self) -> List[Dict[str, Any]]:
        """Format tools for Ollama API."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
            for tool in self.tools
        ]
    
    def chat(self, message: str) -> str:
        """Send a message to the LLM and get a response."""
        # Add user message to conversation history
        self.conversation_history.append({"role": "user", "content": message})
        
        # Prepare the request for Ollama
        request_data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self._create_system_prompt()}
            ] + self.conversation_history,
            "tools": self._format_tool_calls(),
            "stream": False
        }
        
        try:
            # Send request to Ollama
            response = requests.post(
                f"{self.base_url}/chat/completions",
                json=request_data,
                timeout=120
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Check if the LLM wants to call a tool
            if "tool_calls" in result.get("choices", [{}])[0].get("message", {}):
                tool_calls = result["choices"][0]["message"]["tool_calls"]
                tool_results = []
                
                for tool_call in tool_calls:
                    tool_name = tool_call["function"]["name"]
                    arguments_str = tool_call["function"].get("arguments", "{}")
                    
                    # Parse arguments if it's a string
                    try:
                        arguments = json.loads(arguments_str) if isinstance(arguments_str, str) else arguments_str
                    except json.JSONDecodeError:
                        arguments = {}
                    
                    # Call the tool
                    tool_result = self._call_tool(tool_name, arguments)
                    tool_results.append({
                        "tool_call_id": tool_call.get("id", ""),
                        "name": tool_name,
                        "result": tool_result
                    })
                
                # Add assistant message with tool calls to history
                self.conversation_history.append(result["choices"][0]["message"])
                
                # Add tool results to history
                for tool_result in tool_results:
                    self.conversation_history.append({
                        "role": "tool",
                        "tool_call_id": tool_result["tool_call_id"],
                        "content": json.dumps(tool_result["result"])
                    })
                
                # Get final response from LLM
                final_request = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": self._create_system_prompt()}
                    ] + self.conversation_history,
                    "stream": False
                }
                
                final_response = requests.post(
                    f"{self.base_url}/chat/completions",
                    json=final_request,
                    timeout=120
                )
                final_response.raise_for_status()
                
                final_result = final_response.json()
                assistant_message = final_result["choices"][0]["message"]["content"]
                
                # Add final assistant message to history
                self.conversation_history.append({"role": "assistant", "content": assistant_message})
                
                return assistant_message
            else:
                # No tool calls, just return the response
                assistant_message = result["choices"][0]["message"]["content"]
                self.conversation_history.append({"role": "assistant", "content": assistant_message})
                return assistant_message
                
        except requests.exceptions.RequestException as e:
            return f"Error communicating with Ollama: {str(e)}"
        except Exception as e:
            return f"Error processing response: {str(e)}"
    
    def clear_history(self):
        """Clear the conversation history."""
        self.conversation_history = []


def chat_with_ollama(api: PRTAPI, message: str = None) -> str:
    """Convenience function to chat with Ollama LLM."""
    llm = OllamaLLM(api)
    
    if message:
        return llm.chat(message)
    else:
        return "Ollama LLM initialized. You can now chat with me about your contacts and relationships!"


def start_ollama_chat(api: PRTAPI):
    """Start an interactive chat session with Ollama."""
    from rich.console import Console
    from rich.prompt import Prompt
    
    console = Console()
    llm = OllamaLLM(api)
    
    console.print("🤖 Ollama LLM Chat Mode", style="bold blue")
    console.print("Type 'quit' to exit, 'clear' to clear history", style="cyan")
    console.print("=" * 50, style="blue")
    
    while True:
        try:
            user_input = Prompt.ask("\n[bold green]You[/bold green]")
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                console.print("Goodbye!", style="green")
                break
            elif user_input.lower() == 'clear':
                llm.clear_history()
                console.print("Chat history cleared.", style="yellow")
                continue
            elif not user_input.strip():
                continue
            
            console.print("\n[bold blue]Assistant[/bold blue]")
            response = llm.chat(user_input)
            console.print(response, style="white")
            
        except KeyboardInterrupt:
            console.print("\nGoodbye!", style="green")
            break
        except Exception as e:
            console.print(f"Error: {e}", style="red")
