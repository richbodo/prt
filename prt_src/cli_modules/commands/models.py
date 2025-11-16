"""
Models command for PRT CLI.

This module contains the command for listing available LLM models with support status.
"""

import typer
from rich.console import Console
from rich.table import Table

console = Console()


def list_models_command():
    """List available LLM models with support status and hardware requirements."""
    try:
        from prt_src.llm_factory import get_registry
        from prt_src.llm_supported_models import get_hardware_guidance
        from prt_src.llm_supported_models import get_model_support_info
        from prt_src.llm_supported_models import get_recommended_model

        console.print("🔍 Discovering available models...\n", style="bold blue")

        registry = get_registry()

        # Check if Ollama is available
        if not registry.is_available():
            console.print("⚠️  Ollama is not running or not accessible", style="yellow")
            console.print("   Make sure Ollama is running: brew services start ollama", style="dim")
            console.print("   Install Ollama: https://ollama.com/", style="dim")
            raise typer.Exit(1) from None

        # List all models
        models = registry.list_models(force_refresh=True)

        if not models:
            console.print("No models found in Ollama", style="yellow")
            recommended = get_recommended_model()
            console.print(
                f"   Install recommended model: ollama pull {recommended.model_name}", style="dim"
            )
            console.print("   Install any model: ollama pull llama3", style="dim")
            raise typer.Exit(1) from None

        # Create enhanced table with support status and hardware info
        table = Table(title="Available Models", show_header=True)
        table.add_column("Alias", style="cyan", no_wrap=True, width=20)
        table.add_column("Full Name", style="white", width=25)
        table.add_column("Size", style="green", justify="right", width=10)
        table.add_column("Support", style="bright_white", justify="center", width=12)
        table.add_column("Hardware Requirements", style="yellow", width=40)

        # Get default model
        default_model = registry.get_default_model()

        # Sort models: supported first, then by support status, then by name
        def sort_key(model):
            support_info = get_model_support_info(model.name) or get_model_support_info(
                model.friendly_name
            )
            if support_info:
                status_priority = {"official": 0, "experimental": 1, "deprecated": 2}
                return (0, status_priority.get(support_info.support_status, 3), model.name)
            else:
                return (1, 3, model.name)  # Unsupported models last

        sorted_models = sorted(models, key=sort_key)

        # Add rows
        for model in sorted_models:
            # Check support status
            support_info = get_model_support_info(model.name) or get_model_support_info(
                model.friendly_name
            )

            # Format alias with indicators
            alias = model.friendly_name
            if model.name == default_model:
                alias = f"⭐ {alias}"

            # Support status styling
            if support_info:
                if support_info.support_status == "official":
                    support_text = "✅ Official"
                    support_style = "green"
                elif support_info.support_status == "experimental":
                    support_text = "🧪 Experimental"
                    support_style = "yellow"
                elif support_info.support_status == "deprecated":
                    support_text = "⚠️ Deprecated"
                    support_style = "red"
                else:
                    support_text = support_info.support_status.title()
                    support_style = "white"

                # Hardware requirements
                hardware_text = get_hardware_guidance(support_info)
            else:
                support_text = "❓ Unsupported"
                support_style = "dim"
                # Basic hardware info for unsupported models
                model_type = "Local GGUF" if model.is_local_gguf() else "Ollama"
                hardware_text = f"Type: {model_type} | Size: {model.size_human}"

            table.add_row(
                alias,
                model.name,
                model.size_human,
                f"[{support_style}]{support_text}[/]",
                hardware_text,
            )

        console.print(table)
        console.print()

        # Show recommendations and usage
        console.print("🎯 Recommendations:", style="bold blue")

        # Show officially supported models
        official_models = [
            m
            for m in sorted_models
            if (get_model_support_info(m.name) or get_model_support_info(m.friendly_name))
            and (
                get_model_support_info(m.name) or get_model_support_info(m.friendly_name)
            ).support_status
            == "official"
        ]

        if official_models:
            console.print("   ✅ Officially supported (recommended):", style="green")
            for model in official_models[:3]:  # Show top 3
                support_info = get_model_support_info(model.name) or get_model_support_info(
                    model.friendly_name
                )
                console.print(
                    f"      • {support_info.display_name} ({model.friendly_name}) - {support_info.description}",
                    style="white",
                )

        console.print()
        console.print("💡 Usage:", style="bold blue")
        console.print("   Use an alias with --model flag:", style="white")
        if official_models:
            example_model = official_models[0].friendly_name
        else:
            example_model = sorted_models[0].friendly_name
        console.print(f"   python -m prt_src.cli --model {example_model} chat", style="cyan")
        console.print(f"   python -m prt_src.tui --model {example_model}", style="cyan")
        console.print()
        console.print("📋 Legend:", style="bold blue")
        console.print("   ⭐ = Default model (used when --model not specified)", style="dim")
        console.print("   ✅ = Officially supported (all features work)", style="green")
        console.print("   🧪 = Experimental support (some features may not work)", style="yellow")
        console.print("   ❓ = Unsupported (use at your own risk)", style="dim")

    except Exception as e:
        console.print(f"✗ Failed to list models: {e}", style="red")
        console.print("\n💡 Troubleshooting:", style="bold blue")
        console.print("   • Ensure Ollama is installed: https://ollama.com/", style="dim")
        console.print("   • Start Ollama: brew services start ollama", style="dim")
        console.print("   • Check if models are installed: ollama list", style="dim")
        raise typer.Exit(1) from None
