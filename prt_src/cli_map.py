"""
CLI Map Generator for PRT

This module provides functionality to visualize the CLI command structure
and interactive menu hierarchy as a tree.
"""

import typer
from typing import Dict, List, Any, Optional
from rich.console import Console
from rich.tree import Tree
from rich.text import Text
from rich.panel import Panel
import inspect
from pathlib import Path

console = Console()


class CLIMapper:
    """Generate and display CLI command maps."""
    
    def __init__(self, typer_app: typer.Typer):
        self.app = typer_app
        self.commands = {}
        self.interactive_menu = {}
        
    def discover_commands(self) -> Dict[str, Any]:
        """Discover all Typer commands and their metadata."""
        commands = {}
        
        # Get all registered commands from the Typer app
        if hasattr(self.app, 'registered_commands'):
            registered_commands = self.app.registered_commands
            
            # Handle both dict and list formats
            if isinstance(registered_commands, dict):
                command_list = registered_commands.values()
            elif isinstance(registered_commands, list):
                command_list = registered_commands
            else:
                command_list = []
                
            for command_info in command_list:
                if hasattr(command_info, 'callback') and command_info.callback:
                    cmd_name = getattr(command_info, 'name', None) or command_info.callback.__name__
                    
                    # Get command details
                    commands[cmd_name] = {
                        'name': cmd_name,
                        'help': getattr(command_info, 'help', None) or self._extract_docstring(command_info.callback),
                        'params': self._extract_parameters(command_info.callback),
                        'callback': command_info.callback.__name__
                    }
        
        # If no registered commands found, try to extract from known command names
        if not commands:
            # Manually define known commands as fallback
            known_commands = {
                'run': 'Run the interactive CLI',
                'setup': 'Set up PRT configuration and database', 
                'db-status': 'Check the encryption status of the database',
                'encrypt-db': 'Encrypt the database',
                'decrypt-db': 'Decrypt the database', 
                'test': 'Test database connection and credentials',
                'migrate': 'Migrate database schema to latest version',
                'map': 'Display a map of all CLI commands and menu structure'
            }
            
            for cmd_name, description in known_commands.items():
                commands[cmd_name] = {
                    'name': cmd_name,
                    'help': description,
                    'params': [],
                    'callback': cmd_name.replace('-', '_')
                }
                    
        return commands
    
    def _extract_docstring(self, func) -> str:
        """Extract docstring from function."""
        if func.__doc__:
            # Get first line of docstring
            lines = func.__doc__.strip().split('\n')
            return lines[0] if lines else ""
        return "No description available"
    
    def _extract_parameters(self, func) -> List[Dict[str, str]]:
        """Extract parameter information from function signature."""
        params = []
        try:
            sig = inspect.signature(func)
            for param_name, param in sig.parameters.items():
                if param_name not in ['ctx', 'self']:  # Skip common framework params
                    param_info = {
                        'name': param_name,
                        'type': str(param.annotation) if param.annotation != param.empty else 'Any',
                        'default': str(param.default) if param.default != param.empty else None,
                        'required': param.default == param.empty
                    }
                    params.append(param_info)
        except Exception:
            pass  # If signature inspection fails, just return empty list
        return params
    
    def define_interactive_menu(self) -> Dict[str, Any]:
        """Define the interactive menu structure manually."""
        # This represents your current interactive menu structure
        menu_structure = {
            "name": "Interactive Menu",
            "description": "Main interactive interface (python -m prt_src.cli run)",
            "options": {
                "1": {
                    "name": "View Contacts",
                    "description": "Browse and view contact information",
                    "handler": "handle_contacts_view"
                },
                "2": {
                    "name": "Search Contacts", 
                    "description": "Search contacts by various criteria",
                    "handler": "handle_contacts_search"
                },
                "3": {
                    "name": "Import Google Contacts from Takeout",
                    "description": "Import contacts with images from Google Takeout zip file",
                    "handler": "handle_import_google_takeout"
                },
                "4": {
                    "name": "View Tags",
                    "description": "Browse and manage contact tags",
                    "handler": "handle_view_tags"
                },
                "5": {
                    "name": "View Notes",
                    "description": "Browse and manage contact notes", 
                    "handler": "handle_view_notes"
                },
                "6": {
                    "name": "Start LLM Chat",
                    "description": "Enter AI-powered chat mode for contact queries",
                    "handler": "chat"
                },
                "7": {
                    "name": "Database Status",
                    "description": "Check database status and statistics",
                    "handler": "handle_database_status"
                },
                "8": {
                    "name": "Database Backup",
                    "description": "Create database backup",
                    "handler": "handle_database_backup"
                },
                "9": {
                    "name": "Encrypt Database",
                    "description": "Encrypt the database for security",
                    "handler": "handle_encrypt_database"
                },
                "10": {
                    "name": "Decrypt Database",
                    "description": "Decrypt the database (emergency use)",
                    "handler": "handle_decrypt_database"
                },
                "0": {
                    "name": "Exit",
                    "description": "Exit the application",
                    "handler": "exit"
                }
            }
        }
        return menu_structure
    
    def generate_tree(self, show_params: bool = False) -> Tree:
        """Generate a Rich Tree representation of the CLI structure."""
        
        # Create root tree
        root = Tree(
            Text("🗺️  PRT CLI Map", style="bold blue"),
            guide_style="blue"
        )
        
        # Add direct commands section
        commands = self.discover_commands()
        if commands:
            cmd_branch = root.add(
                Text("📋 Direct Commands", style="bold green"),
                guide_style="green"
            )
            
            for cmd_name, cmd_info in sorted(commands.items()):
                cmd_text = Text()
                cmd_text.append(f"python -m prt_src.cli {cmd_name}", style="cyan bold")
                
                if cmd_info.get('help'):
                    cmd_text.append(f" - {cmd_info['help']}", style="white")
                
                cmd_node = cmd_branch.add(cmd_text)
                
                # Add parameters if requested
                if show_params and cmd_info.get('params'):
                    params_node = cmd_node.add(Text("Parameters:", style="yellow"))
                    for param in cmd_info['params']:
                        param_text = Text()
                        param_text.append(f"--{param['name']}", style="magenta")
                        param_text.append(f" ({param['type']})", style="dim")
                        if param.get('default'):
                            param_text.append(f" = {param['default']}", style="dim cyan")
                        if param['required']:
                            param_text.append(" [required]", style="red")
                        params_node.add(param_text)
        
        # Add interactive menu section
        menu = self.define_interactive_menu()
        menu_branch = root.add(
            Text("🎯 Interactive Menu", style="bold magenta"),
            guide_style="magenta"
        )
        
        menu_desc = menu_branch.add(
            Text(f"{menu['description']}", style="cyan italic")
        )
        
        for option_key, option_info in menu['options'].items():
            option_text = Text()
            option_text.append(f"[{option_key}] ", style="yellow bold")
            option_text.append(f"{option_info['name']}", style="white bold")
            option_text.append(f" - {option_info['description']}", style="dim white")
            
            option_node = menu_branch.add(option_text)
            
            # Add handler info
            if show_params:
                handler_text = Text()
                handler_text.append("Handler: ", style="dim")
                handler_text.append(option_info['handler'], style="dim cyan")
                option_node.add(handler_text)
        
        return root
    
    def display_map(self, show_params: bool = False, format_type: str = "tree"):
        """Display the CLI map in the specified format."""
        
        if format_type == "tree":
            tree = self.generate_tree(show_params=show_params)
            console.print()
            console.print(tree)
            console.print()
            
        elif format_type == "text":
            self._display_text_map(show_params)
            
        # Add usage examples
        examples_panel = Panel(
            "[cyan]Usage Examples:[/cyan]\n\n"
            "[yellow]Direct commands:[/yellow]\n"
            "  python -m prt_src.cli setup\n"
            "  python -m prt_src.cli db-status\n"
            "  python -m prt_src.cli run\n\n"
            "[yellow]Interactive mode:[/yellow]\n"
            "  python -m prt_src.cli run\n"
            "  # Then select option 1-10 from the menu\n\n"
            "[yellow]Show detailed map:[/yellow]\n"
            "  python -m prt_src.cli map --show-params",
            title="💡 Usage Guide",
            title_align="left",
            border_style="blue"
        )
        console.print(examples_panel)
    
    def _display_text_map(self, show_params: bool = False):
        """Display map in plain text format."""
        console.print("\n[bold blue]🗺️  PRT CLI Map[/bold blue]\n")
        
        # Direct commands
        commands = self.discover_commands()
        console.print("[bold green]📋 Direct Commands:[/bold green]")
        for cmd_name, cmd_info in sorted(commands.items()):
            console.print(f"  [cyan]python -m prt_src.cli {cmd_name}[/cyan] - {cmd_info.get('help', 'No description')}")
            
            if show_params and cmd_info.get('params'):
                for param in cmd_info['params']:
                    req_str = "[red](required)[/red]" if param['required'] else f"[dim cyan](default: {param.get('default', 'None')})[/dim cyan]"
                    console.print(f"    [magenta]--{param['name']}[/magenta] ({param['type']}) {req_str}")
        
        # Interactive menu
        console.print(f"\n[bold magenta]🎯 Interactive Menu:[/bold magenta]")
        menu = self.define_interactive_menu()
        console.print(f"  [cyan italic]{menu['description']}[/cyan italic]")
        
        for option_key, option_info in menu['options'].items():
            console.print(f"    [{option_key}] [white bold]{option_info['name']}[/white bold] - {option_info['description']}")
            if show_params:
                console.print(f"        [dim cyan]Handler: {option_info['handler']}[/dim cyan]")


def create_map_command(typer_app: typer.Typer):
    """Create and return the map command function."""
    
    def map_command(
        show_params: bool = typer.Option(False, "--show-params", "-p", help="Show detailed parameter information"),
        format_type: str = typer.Option("tree", "--format", "-f", help="Output format: 'tree' or 'text'")
    ):
        """🗺️  Display a map of all CLI commands and menu structure."""
        mapper = CLIMapper(typer_app)
        mapper.display_map(show_params=show_params, format_type=format_type)
    
    return map_command
