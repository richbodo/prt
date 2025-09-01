"""First-run wizard screen for PRT TUI.

Shows welcome screen, creates "You" contact, and offers to load demo data.
Only shows when no "You" contact exists.
"""

from typing import Optional

from textual import events, on
from textual.app import ComposeResult
from textual.containers import Center, Container, Horizontal, Vertical
from textual.widgets import Button, Input, Label, Static

from prt_src.logging_config import get_logger
from prt_src.tui.screens import register_screen
from prt_src.tui.screens.base import BaseScreen, EscapeIntent

logger = get_logger(__name__)


class WizardScreen(BaseScreen):
    """First-run wizard screen."""

    # Wizard steps
    STEP_WELCOME = 0
    STEP_CREATE_YOU = 1
    STEP_OPTIONS = 2
    STEP_COMPLETE = 3

    def __init__(self, *args, **kwargs):
        """Initialize wizard screen."""
        super().__init__(*args, **kwargs)

        # Wizard state
        self.current_step = self.STEP_WELCOME
        self.you_contact_name = ""
        self.you_contact_created = False

        # Widget references
        self.content_container: Optional[Container] = None
        self.name_input: Optional[Input] = None

    def get_screen_name(self) -> str:
        """Get screen identifier."""
        return "wizard"

    def on_escape(self) -> EscapeIntent:
        """ESC intent depends on current step."""
        if self.current_step == self.STEP_WELCOME:
            # Can't escape welcome step easily - go to complete step to skip
            return EscapeIntent.CUSTOM
        else:
            # Other steps can go back or to home
            return EscapeIntent.HOME

    def handle_custom_escape(self) -> None:
        """Handle custom escape behavior."""
        if self.current_step == self.STEP_WELCOME:
            # Skip to complete step
            self.current_step = self.STEP_COMPLETE
            self.call_later(self._render_current_step)

    def get_header_config(self) -> dict:
        """Configure header with title."""
        config = super().get_header_config()
        if config:
            config["title"] = "Welcome to PRT"
        return config

    def get_footer_config(self) -> dict:
        """Configure footer with step-specific hints."""
        config = super().get_footer_config()
        if config:
            if self.current_step == self.STEP_WELCOME:
                config["keyHints"] = [
                    "[Enter] Continue",
                    "[ESC] Skip Setup",
                ]
            elif self.current_step == self.STEP_CREATE_YOU:
                config["keyHints"] = [
                    "[Enter] Create",
                    "[ESC] Skip",
                ]
            elif self.current_step == self.STEP_OPTIONS:
                config["keyHints"] = [
                    "[Enter] Select",
                    "[ESC] Skip",
                ]
            elif self.current_step == self.STEP_COMPLETE:
                config["keyHints"] = [
                    "[Enter] Continue to PRT",
                ]
        return config

    def compose(self) -> ComposeResult:
        """Compose wizard screen layout."""
        with Center(id="wizard-center"):
            with Container(id="wizard-container", classes="wizard-main"):
                # Content container will be dynamically populated based on current step
                with Container(id="wizard-content") as self.content_container:
                    yield Static("Loading...", id="wizard-loading")

    async def on_mount(self) -> None:
        """Initialize wizard when screen is mounted."""
        await super().on_mount()
        await self._render_current_step()

    async def on_show(self) -> None:
        """Show wizard when screen becomes visible."""
        await super().on_show()
        # Reset to welcome step if needed
        if self.current_step == self.STEP_COMPLETE and not self.you_contact_created:
            self.current_step = self.STEP_WELCOME
            await self._render_current_step()

    async def _render_current_step(self) -> None:
        """Render the current wizard step."""
        if not self.content_container:
            return

        # Clear existing content
        await self.content_container.remove_children()

        # Render step-specific content
        if self.current_step == self.STEP_WELCOME:
            await self._render_welcome_step()
        elif self.current_step == self.STEP_CREATE_YOU:
            await self._render_create_you_step()
        elif self.current_step == self.STEP_OPTIONS:
            await self._render_options_step()
        elif self.current_step == self.STEP_COMPLETE:
            await self._render_complete_step()

    async def _render_welcome_step(self) -> None:
        """Render welcome step."""
        await self.content_container.mount_all(
            [
                Vertical(
                    Label("🎉 Welcome to PRT!", classes="wizard-title"),
                    Label("Personal Relationship Tracker", classes="wizard-subtitle"),
                    Static(""),
                    Label(
                        "PRT helps you manage your personal contacts and relationships.\n"
                        "This quick setup will get you started.",
                        classes="wizard-description",
                    ),
                    Static(""),
                    Label("Features:", classes="wizard-features-title"),
                    Label("• Store and organize your contacts", classes="wizard-feature"),
                    Label("• Track relationships between people", classes="wizard-feature"),
                    Label("• Tag contacts and add notes", classes="wizard-feature"),
                    Label("• Search across all your data", classes="wizard-feature"),
                    Label("• Import from Google Takeout", classes="wizard-feature"),
                    Label("• Chat with AI about your network", classes="wizard-feature"),
                    Static(""),
                    Button(
                        "Get Started",
                        id="welcome-continue",
                        variant="primary",
                        classes="wizard-button",
                    ),
                    Button(
                        "Skip Setup",
                        id="welcome-skip",
                        variant="default",
                        classes="wizard-button-secondary",
                    ),
                    classes="wizard-step",
                )
            ]
        )

        # Focus the continue button
        continue_btn = self.query_one("#welcome-continue", Button)
        continue_btn.focus()

    async def _render_create_you_step(self) -> None:
        """Render create "You" contact step."""
        await self.content_container.mount_all(
            [
                Vertical(
                    Label("👤 Create Your Profile", classes="wizard-title"),
                    Static(""),
                    Label(
                        "First, let's create a contact record for you.\n"
                        "This helps establish relationships in your network.",
                        classes="wizard-description",
                    ),
                    Static(""),
                    Label("Your Name:", classes="form-label"),
                    Input(
                        placeholder="Enter your full name...",
                        id="you-name-input",
                        classes="wizard-input",
                    ),
                    Static(""),
                    Horizontal(
                        Button(
                            "Create Profile",
                            id="create-you",
                            variant="primary",
                            classes="wizard-button",
                        ),
                        Button(
                            "Skip",
                            id="skip-you",
                            variant="default",
                            classes="wizard-button-secondary",
                        ),
                        classes="wizard-buttons",
                    ),
                    classes="wizard-step",
                )
            ]
        )

        # Store reference to name input and focus it
        self.name_input = self.query_one("#you-name-input", Input)
        self.name_input.focus()

    async def _render_options_step(self) -> None:
        """Render options step."""
        await self.content_container.mount_all(
            [
                Vertical(
                    Label("⚡ Quick Start Options", classes="wizard-title"),
                    Static(""),
                    Label(
                        "Choose how you'd like to get started with PRT:",
                        classes="wizard-description",
                    ),
                    Static(""),
                    Button(
                        "📥 Import Google Takeout",
                        id="import-takeout",
                        variant="primary",
                        classes="wizard-option-button",
                    ),
                    Label(
                        "Import your contacts from Google Takeout archive",
                        classes="wizard-option-description",
                    ),
                    Static(""),
                    Button(
                        "🧪 Load Demo Data",
                        id="load-demo",
                        variant="default",
                        classes="wizard-option-button",
                    ),
                    Label(
                        "Load sample contacts and relationships to explore PRT",
                        classes="wizard-option-description",
                    ),
                    Static(""),
                    Button(
                        "✨ Start Empty",
                        id="start-empty",
                        variant="default",
                        classes="wizard-option-button",
                    ),
                    Label(
                        "Start with an empty database and add contacts manually",
                        classes="wizard-option-description",
                    ),
                    classes="wizard-step",
                )
            ]
        )

        # Focus the first option
        import_btn = self.query_one("#import-takeout", Button)
        import_btn.focus()

    async def _render_complete_step(self) -> None:
        """Render completion step."""
        if self.you_contact_created:
            welcome_message = f"Welcome to PRT, {self.you_contact_name}! 🎉"
            description = "Your profile has been created and you're ready to explore PRT."
        else:
            welcome_message = "Welcome to PRT! 🎉"
            description = "You're ready to explore PRT. You can create your profile later from the contacts screen."

        await self.content_container.mount_all(
            [
                Vertical(
                    Label(welcome_message, classes="wizard-title"),
                    Static(""),
                    Label(description, classes="wizard-description"),
                    Static(""),
                    Label("🚀 Quick Tips:", classes="wizard-features-title"),
                    Label("• Press 'h' to go to the home screen", classes="wizard-feature"),
                    Label("• Press 'c' to manage contacts", classes="wizard-feature"),
                    Label("• Press 's' to search your data", classes="wizard-feature"),
                    Label("• Press '?' for help anytime", classes="wizard-feature"),
                    Label("• Press 'ESC' to navigate between screens", classes="wizard-feature"),
                    Static(""),
                    Button(
                        "Continue to PRT",
                        id="finish-wizard",
                        variant="primary",
                        classes="wizard-button",
                    ),
                    classes="wizard-step",
                )
            ]
        )

        # Focus the finish button
        finish_btn = self.query_one("#finish-wizard", Button)
        finish_btn.focus()

    # Event handlers

    async def on_key(self, event: events.Key) -> None:
        """Handle key presses."""
        key = event.key

        if key == "enter":
            # Handle enter key for current step
            await self._handle_enter()
        else:
            # Let parent handle other keys
            await super().on_key(event)

    async def _handle_enter(self) -> None:
        """Handle enter key based on current step."""
        if self.current_step == self.STEP_WELCOME:
            await self._continue_from_welcome()
        elif self.current_step == self.STEP_CREATE_YOU:
            await self._create_you_contact()
        elif self.current_step == self.STEP_OPTIONS:
            # Focus on the primary option button
            try:
                import_btn = self.query_one("#import-takeout", Button)
                if import_btn.has_focus:
                    await self._handle_import_takeout()
                else:
                    # Just focus the import button
                    import_btn.focus()
            except Exception:
                pass
        elif self.current_step == self.STEP_COMPLETE:
            await self._finish_wizard()

    # Button event handlers

    @on(Button.Pressed, "#welcome-continue")
    async def on_welcome_continue(self, message: Button.Pressed) -> None:
        """Handle welcome continue button."""
        await self._continue_from_welcome()

    @on(Button.Pressed, "#welcome-skip")
    async def on_welcome_skip(self, message: Button.Pressed) -> None:
        """Handle welcome skip button."""
        await self._skip_to_complete()

    @on(Button.Pressed, "#create-you")
    async def on_create_you(self, message: Button.Pressed) -> None:
        """Handle create you button."""
        await self._create_you_contact()

    @on(Button.Pressed, "#skip-you")
    async def on_skip_you(self, message: Button.Pressed) -> None:
        """Handle skip you button."""
        await self._skip_create_you()

    @on(Button.Pressed, "#import-takeout")
    async def on_import_takeout(self, message: Button.Pressed) -> None:
        """Handle import takeout button."""
        await self._handle_import_takeout()

    @on(Button.Pressed, "#load-demo")
    async def on_load_demo(self, message: Button.Pressed) -> None:
        """Handle load demo button."""
        await self._handle_load_demo()

    @on(Button.Pressed, "#start-empty")
    async def on_start_empty(self, message: Button.Pressed) -> None:
        """Handle start empty button."""
        await self._handle_start_empty()

    @on(Button.Pressed, "#finish-wizard")
    async def on_finish_wizard(self, message: Button.Pressed) -> None:
        """Handle finish wizard button."""
        await self._finish_wizard()

    # Step transition methods

    async def _continue_from_welcome(self) -> None:
        """Continue from welcome step."""
        self.current_step = self.STEP_CREATE_YOU
        await self._render_current_step()

    async def _skip_to_complete(self) -> None:
        """Skip to complete step."""
        self.current_step = self.STEP_COMPLETE
        await self._render_current_step()

    async def _create_you_contact(self) -> None:
        """Create the 'You' contact."""
        if not self.name_input or not self.data_service:
            await self._skip_create_you()
            return

        name = self.name_input.value.strip()
        if not name:
            if self.notification_service:
                self.notification_service.show_warning("Please enter your name")
            return

        try:
            # Create the "You" contact using the app's first-run handler
            if hasattr(self.app, "first_run_handler"):
                contact = self.app.first_run_handler.create_you_contact(name)
                if contact:
                    self.you_contact_name = name
                    self.you_contact_created = True
                    if self.notification_service:
                        self.notification_service.show_success(f"Welcome, {name}!")

                    # Continue to options
                    self.current_step = self.STEP_OPTIONS
                    await self._render_current_step()
                else:
                    if self.notification_service:
                        self.notification_service.show_error("Failed to create your profile")
            else:
                # Fallback to creating through data service
                contact_data = {
                    "first_name": name.split()[0] if name.split() else "You",
                    "last_name": " ".join(name.split()[1:]) if len(name.split()) > 1 else "",
                    "is_you": True,
                }

                contact = await self.data_service.create_contact(contact_data)
                if contact:
                    self.you_contact_name = name
                    self.you_contact_created = True
                    if self.notification_service:
                        self.notification_service.show_success(f"Welcome, {name}!")

                    # Continue to options
                    self.current_step = self.STEP_OPTIONS
                    await self._render_current_step()
                else:
                    if self.notification_service:
                        self.notification_service.show_error("Failed to create your profile")

        except Exception as e:
            logger.error(f"Failed to create 'You' contact: {e}")
            if self.notification_service:
                self.notification_service.show_error("Failed to create your profile")

    async def _skip_create_you(self) -> None:
        """Skip creating You contact."""
        self.current_step = self.STEP_OPTIONS
        await self._render_current_step()

    async def _handle_import_takeout(self) -> None:
        """Handle import Google Takeout option."""
        if self.notification_service:
            self.notification_service.show_info("Navigating to import screen...")

        # Navigate to import screen
        if self.nav_service:
            self.nav_service.push("import")

        # Switch to import screen
        if hasattr(self.app, "switch_screen"):
            await self.app.switch_screen("import")

    async def _handle_load_demo(self) -> None:
        """Handle load demo data option."""
        try:
            if self.notification_service:
                self.notification_service.show_info("Loading demo data...")

            # Load demo fixtures using the test fixtures
            from tests.fixtures import create_fixture_data

            if self.data_service and self.data_service.api:
                # Create demo data using the fixture system
                fixture_data = create_fixture_data(self.data_service.api.db)

                if fixture_data:
                    if self.notification_service:
                        contacts_count = len(fixture_data.get("contacts", []))
                        self.notification_service.show_success(
                            f"Loaded {contacts_count} demo contacts with relationships!"
                        )
                else:
                    if self.notification_service:
                        self.notification_service.show_warning("Demo data may already exist")

            # Continue to complete step
            self.current_step = self.STEP_COMPLETE
            await self._render_current_step()

        except Exception as e:
            logger.error(f"Failed to load demo data: {e}")
            if self.notification_service:
                self.notification_service.show_error("Failed to load demo data")

            # Still continue to complete step
            self.current_step = self.STEP_COMPLETE
            await self._render_current_step()

    async def _handle_start_empty(self) -> None:
        """Handle start empty option."""
        if self.notification_service:
            self.notification_service.show_info("Starting with empty database")

        # Go directly to complete step
        self.current_step = self.STEP_COMPLETE
        await self._render_current_step()

    async def _finish_wizard(self) -> None:
        """Finish wizard and go to home screen."""
        if self.notification_service:
            self.notification_service.show_success("Setup complete! Welcome to PRT!")

        # Navigate to home screen
        if self.nav_service:
            self.nav_service.go_home()

        # Switch to home screen
        if hasattr(self.app, "switch_screen"):
            await self.app.switch_screen("home")


# Register this screen
register_screen("wizard", WizardScreen)
