"""
LLM integration services for PRT CLI.

Functions for managing LLM chat interactions and providing chat interface.
These functions handle the interactive chat experience with various LLM providers.
"""

from rich.console import Console
from rich.prompt import Prompt


def start_llm_chat(llm, api, initial_prompt: str = None):
    """Start an interactive chat session with any LLM provider.

    This is a generic chat function that works with both OllamaLLM and LlamaCppLLM.

    Args:
        llm: LLM instance (OllamaLLM or LlamaCppLLM)
        api: PRTAPI instance
        initial_prompt: Optional initial prompt to send immediately
    """
    console = Console()

    console.print("🤖 LLM Chat Mode", style="bold blue")
    console.print(
        "Type 'quit' to exit, 'clear' to clear history, 'help' for assistance", style="cyan"
    )
    console.print("=" * 50, style="blue")

    # Handle initial prompt if provided
    if initial_prompt:
        console.print(f"\n[bold green]You[/bold green]: {initial_prompt}")
        console.print("\n[bold blue]Assistant[/bold blue]")
        console.print("Thinking...", style="dim")
        try:
            response = llm.chat(initial_prompt)
            console.print(response, style="white")
        except Exception as e:
            console.print(f"Error processing initial prompt: {e}", style="red")

    while True:
        try:
            user_input = Prompt.ask("\n[bold green]You[/bold green]")

            if user_input.lower() in ["quit", "exit", "q"]:
                console.print("Goodbye!", style="green")
                break
            elif user_input.lower() == "clear":
                llm.clear_history()
                console.print("Chat history cleared.", style="yellow")
                continue
            elif user_input.lower() == "help":
                console.print("\n[bold blue]Available Commands:[/bold blue]")
                console.print("- Type your questions about contacts, tags, or notes", style="white")
                console.print("- 'clear': Clear chat history", style="white")
                console.print("- 'quit' or 'exit': Exit chat mode", style="white")
                console.print("\n[bold blue]Example Questions:[/bold blue]")
                console.print("- 'Show me all contacts'", style="white")
                console.print("- 'Find contacts named John'", style="white")
                console.print("- 'What tags do I have?'", style="white")
                console.print("- 'How many contacts do I have?'", style="white")
                continue
            elif not user_input.strip():
                continue

            console.print("\n[bold blue]Assistant[/bold blue]")
            console.print("Thinking...", style="dim")
            response = llm.chat(user_input)
            console.print(response, style="white")

        except (KeyboardInterrupt, EOFError):
            console.print("\nGoodbye!", style="green")
            break
        except Exception as e:
            console.print(f"Error: {e}", style="red")
            console.print(
                "Try asking a simpler question or type 'help' for assistance.", style="yellow"
            )
