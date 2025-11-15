"""Unit tests for debug_info module."""

import subprocess
from unittest.mock import Mock
from unittest.mock import patch

from prt_src.debug_info import collect_config_info
from prt_src.debug_info import collect_database_info
from prt_src.debug_info import collect_debug_info
from prt_src.debug_info import collect_llm_info
from prt_src.debug_info import collect_system_environment
from prt_src.debug_info import collect_system_prompt
from prt_src.debug_info import format_debug_output
from prt_src.debug_info import generate_debug_report


class TestCollectSystemEnvironment:
    """Test system environment collection."""

    @patch("prt_src.debug_info.subprocess.run")
    @patch("prt_src.debug_info.platform")
    def test_collect_system_environment_with_ollama(self, mock_platform, mock_subprocess):
        """Test system environment collection when Ollama is available."""
        # Setup mocks
        mock_platform.system.return_value = "Darwin"
        mock_platform.release.return_value = "21.6.0"
        mock_platform.version.return_value = "Darwin Kernel Version 21.6.0"
        mock_platform.machine.return_value = "arm64"
        mock_platform.architecture.return_value = ("64bit", "")
        mock_platform.python_version.return_value = "3.11.0"
        mock_platform.python_implementation.return_value = "CPython"

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "ollama version is 0.1.26"
        mock_subprocess.return_value = mock_result

        # Test
        result = collect_system_environment()

        # Verify
        assert result["os"]["system"] == "Darwin"
        assert result["os"]["machine"] == "arm64"
        assert result["python"]["version"] == "3.11.0"
        assert result["ollama"]["available"] is True
        assert result["ollama"]["version"] == "ollama version is 0.1.26"

    @patch("prt_src.debug_info.subprocess.run")
    def test_collect_system_environment_ollama_not_found(self, mock_subprocess):
        """Test system environment collection when Ollama is not installed."""
        # Setup mock to raise FileNotFoundError (Ollama not found)
        mock_subprocess.side_effect = FileNotFoundError("Command not found")

        # Test
        result = collect_system_environment()

        # Verify
        assert result["ollama"]["available"] is False
        assert "Command not found" in result["ollama"]["error"]

    @patch("prt_src.debug_info.subprocess.run")
    @patch("prt_src.debug_info.platform")
    def test_collect_system_environment_ollama_timeout(self, mock_platform, mock_subprocess):
        """Test system environment collection when Ollama times out."""
        # Setup platform mocks
        mock_platform.system.return_value = "Darwin"
        mock_platform.release.return_value = "21.6.0"
        mock_platform.version.return_value = "Darwin Kernel Version 21.6.0"
        mock_platform.machine.return_value = "arm64"
        mock_platform.architecture.return_value = ("64bit", "")
        mock_platform.python_version.return_value = "3.11.0"
        mock_platform.python_implementation.return_value = "CPython"

        # Setup mock to raise TimeoutExpired
        mock_subprocess.side_effect = subprocess.TimeoutExpired(["ollama", "--version"], timeout=5)

        # Test
        result = collect_system_environment()

        # Verify
        assert result["ollama"]["available"] is False
        assert "timed out" in result["ollama"]["error"]


class TestCollectDatabaseInfo:
    """Test database information collection."""

    @patch("prt_src.debug_info.load_config")
    @patch("prt_src.debug_info.PRTAPI")
    @patch("prt_src.debug_info.SchemaManager")
    def test_collect_database_info_success(
        self, mock_schema_manager, mock_api_class, mock_load_config
    ):
        """Test successful database info collection."""
        # Setup mocks
        mock_config = {"db_path": "/test/path/db.sqlite"}
        mock_load_config.return_value = mock_config

        mock_api = Mock()
        mock_api.test_database_connection.return_value = True
        mock_api.get_data_directory.return_value = "/test/data"
        mock_api.db.count_contacts.return_value = 10
        mock_api.db.count_tags.return_value = 5
        mock_api.db.count_notes.return_value = 3
        mock_api.db.count_relationships.return_value = 8
        mock_api_class.return_value = mock_api

        mock_schema = Mock()
        mock_schema.get_schema_version.return_value = 5
        mock_schema.get_migration_info.return_value = {"status": "current"}
        mock_schema_manager.return_value = mock_schema

        # Test
        result = collect_database_info()

        # Verify
        assert result["status"] == "healthy"
        assert result["connection_test"] is True
        assert result["statistics"]["contacts"] == 10
        assert result["statistics"]["tags"] == 5
        assert result["schema_info"]["current_version"] == 5

    @patch("prt_src.debug_info.load_config")
    def test_collect_database_info_failure(self, mock_load_config):
        """Test database info collection when database is unavailable."""
        # Setup mock to raise exception
        mock_load_config.side_effect = Exception("Config not found")

        # Test
        result = collect_database_info()

        # Verify
        assert result["status"] == "error"
        assert "Config not found" in result["error"]


class TestCollectLLMInfo:
    """Test LLM information collection."""

    @patch("prt_src.debug_info.get_registry")
    @patch("prt_src.debug_info.resolve_model_alias")
    @patch("prt_src.debug_info.check_model_availability")
    def test_collect_llm_info_success(
        self, mock_check_availability, mock_resolve_alias, mock_get_registry
    ):
        """Test successful LLM info collection."""
        # Setup mocks
        mock_registry = Mock()
        mock_registry.is_available.return_value = True
        mock_registry.list_models.return_value = ["gpt-oss:20b", "mistral:7b"]
        mock_get_registry.return_value = mock_registry

        mock_resolve_alias.return_value = "gpt-oss:20b"
        mock_check_availability.return_value = {"available_in_ollama": True, "error": None}

        # Test
        result = collect_llm_info()

        # Verify
        assert result["status"] == "healthy"
        assert result["registry_available"] is True
        assert result["default_model"] == "gpt-oss:20b"
        assert len(result["available_models"]) == 2
        assert result["connectivity_test"]["available"] is True

    @patch("prt_src.debug_info.get_registry")
    def test_collect_llm_info_registry_unavailable(self, mock_get_registry):
        """Test LLM info collection when registry is unavailable."""
        # Setup mock
        mock_registry = Mock()
        mock_registry.is_available.return_value = False
        mock_get_registry.return_value = mock_registry

        # Test
        result = collect_llm_info()

        # Verify
        assert result["status"] == "registry_unavailable"
        assert result["registry_available"] is False
        assert result["available_models"] == []

    @patch("prt_src.debug_info.get_registry")
    def test_collect_llm_info_exception(self, mock_get_registry):
        """Test LLM info collection when an exception occurs."""
        # Setup mock to raise exception
        mock_get_registry.side_effect = Exception("Registry error")

        # Test
        result = collect_llm_info()

        # Verify
        assert result["status"] == "error"
        assert "Registry error" in result["error"]


class TestCollectSystemPrompt:
    """Test system prompt collection."""

    @patch("prt_src.debug_info.load_config")
    @patch("prt_src.debug_info.PRTAPI")
    @patch("prt_src.debug_info.resolve_model_alias")
    @patch("prt_src.llm_ollama.OllamaLLM")
    def test_collect_system_prompt_success(
        self, mock_llm_class, mock_resolve_alias, mock_api_class, mock_load_config
    ):
        """Test successful system prompt collection."""
        # Setup mocks
        mock_config = {"llm": {"timeout": 30}}
        mock_load_config.return_value = mock_config

        mock_api = Mock()
        mock_api_class.return_value = mock_api

        mock_resolve_alias.return_value = "gpt-oss:20b"

        mock_llm = Mock()
        mock_llm._create_system_prompt.return_value = "System prompt content"
        mock_llm_class.return_value = mock_llm

        # Test
        result = collect_system_prompt()

        # Verify
        assert result["status"] == "available"
        assert result["prompt_preview"] == "System prompt content"
        assert result["prompt_length"] == len("System prompt content")

    @patch("prt_src.debug_info.load_config")
    def test_collect_system_prompt_failure(self, mock_load_config):
        """Test system prompt collection when it fails."""
        # Setup mock to raise exception
        mock_load_config.side_effect = Exception("Config error")

        # Test
        result = collect_system_prompt()

        # Verify
        assert result["status"] == "error"
        assert "Config error" in result["error"]

    @patch("prt_src.debug_info.load_config")
    @patch("prt_src.debug_info.PRTAPI")
    @patch("prt_src.debug_info.resolve_model_alias")
    @patch("prt_src.llm_ollama.OllamaLLM")
    def test_collect_system_prompt_long_prompt(
        self, mock_llm_class, mock_resolve_alias, mock_api_class, mock_load_config
    ):
        """Test system prompt collection with very long prompt."""
        # Setup mocks
        mock_config = {"llm": {}}
        mock_load_config.return_value = mock_config

        mock_api = Mock()
        mock_api_class.return_value = mock_api

        mock_resolve_alias.return_value = "gpt-oss:20b"

        mock_llm = Mock()
        long_prompt = "x" * 1000  # 1000 character prompt
        mock_llm._create_system_prompt.return_value = long_prompt
        mock_llm_class.return_value = mock_llm

        # Test
        result = collect_system_prompt()

        # Verify
        assert result["status"] == "available"
        # With the new 6000 char limit, 1000 chars should not be truncated
        assert not result["prompt_preview"].endswith("...")  # Should NOT be truncated
        assert result["prompt_preview"] == long_prompt  # Should be the full prompt
        assert result["prompt_length"] == 1000

    @patch("prt_src.debug_info.load_config")
    @patch("prt_src.debug_info.PRTAPI")
    @patch("prt_src.debug_info.resolve_model_alias")
    @patch("prt_src.llm_ollama.OllamaLLM")
    def test_collect_system_prompt_enhanced_preview(
        self, mock_llm_class, mock_resolve_alias, mock_api_class, mock_load_config
    ):
        """Test that enhanced preview includes tools section."""
        # Setup mocks
        mock_config = {"llm": {}}
        mock_load_config.return_value = mock_config

        mock_api = Mock()
        mock_api_class.return_value = mock_api

        mock_resolve_alias.return_value = "gpt-oss:20b"

        mock_llm = Mock()
        # Create a realistic system prompt with tools section
        long_prompt = (
            "You are PRT Assistant, a specialized AI for managing personal relationships and contacts. "
            * 10
            + "\n\n## AVAILABLE TOOLS\n\nThe following tools are available for database operations:\n\n"
            "### execute_sql\nExecute SQL queries on the database for complex searches and analytics."
            * 20
        )
        mock_llm._create_system_prompt.return_value = long_prompt
        mock_llm_class.return_value = mock_llm

        # Test
        result = collect_system_prompt()

        # Verify
        assert result["status"] == "available"
        assert "AVAILABLE TOOLS" in result["prompt_preview"]
        assert "execute_sql" in result["prompt_preview"]
        assert len(result["prompt_preview"]) > 1000  # Should be longer than old limit
        assert result["prompt_length"] == len(long_prompt)


class TestCollectConfigInfo:
    """Test configuration information collection."""

    @patch("prt_src.config.data_dir")
    @patch("prt_src.debug_info.load_config")
    def test_collect_config_info_success(self, mock_load_config, mock_data_dir):
        """Test successful config info collection."""
        # Setup mocks
        mock_config = {
            "db_path": "/test/db.sqlite",
            "llm": {"model": "gpt-oss:20b", "timeout": 30, "password": "secret123"},
        }
        mock_load_config.return_value = mock_config

        mock_config_path = Mock()
        mock_config_path.exists.return_value = True
        mock_config_path.__str__ = Mock(return_value="/test/config/prt_config.json")

        mock_data_path = Mock()
        mock_data_path.__truediv__ = Mock(return_value=mock_config_path)
        mock_data_dir.return_value = mock_data_path

        # Test
        result = collect_config_info()

        # Verify
        assert result["status"] == "loaded"
        assert result["config_loaded"] is True
        assert result["llm_config"]["model"] == "gpt-oss:20b"
        assert result["llm_config"]["password"] == "[REDACTED]"  # Should be redacted

    @patch("prt_src.debug_info.load_config")
    def test_collect_config_info_failure(self, mock_load_config):
        """Test config info collection when loading fails."""
        # Setup mock to raise exception
        mock_load_config.side_effect = Exception("Config error")

        # Test
        result = collect_config_info()

        # Verify
        assert result["status"] == "error"
        assert "Config error" in result["error"]


class TestCollectDebugInfo:
    """Test main debug info collection orchestration."""

    @patch("prt_src.debug_info.collect_system_environment")
    @patch("prt_src.debug_info.collect_config_info")
    @patch("prt_src.debug_info.collect_database_info")
    @patch("prt_src.debug_info.collect_llm_info")
    @patch("prt_src.debug_info.collect_system_prompt")
    def test_collect_debug_info_orchestration(
        self, mock_prompt, mock_llm, mock_db, mock_config, mock_env
    ):
        """Test that main function calls all collection functions."""
        # Setup mocks
        mock_env.return_value = {"test": "env"}
        mock_config.return_value = {"test": "config"}
        mock_db.return_value = {"test": "db"}
        mock_llm.return_value = {"test": "llm"}
        mock_prompt.return_value = {"test": "prompt"}

        # Test
        result = collect_debug_info()

        # Verify all functions were called
        mock_env.assert_called_once()
        mock_config.assert_called_once()
        mock_db.assert_called_once()
        mock_llm.assert_called_once()
        mock_prompt.assert_called_once()

        # Verify structure
        assert "system_environment" in result
        assert "configuration" in result
        assert "database" in result
        assert "llm" in result
        assert "system_prompt" in result


class TestFormatDebugOutput:
    """Test debug output formatting."""

    def test_format_debug_output_complete(self):
        """Test formatting with complete debug data."""
        debug_data = {
            "system_environment": {
                "os": {"system": "Darwin", "release": "21.6.0", "architecture": "arm64"},
                "python": {
                    "version": "3.11.0",
                    "implementation": "CPython",
                    "executable": "/usr/bin/python",
                },
                "prt_version": "0.1.0",
                "ollama": {"available": True, "version": "ollama version is 0.1.26"},
            },
            "configuration": {
                "status": "loaded",
                "config_path": "/test/config.json",
                "llm_config": {"model": "gpt-oss:20b"},
            },
            "database": {
                "status": "healthy",
                "data_directory": "/test/data",
                "statistics": {"contacts": 10, "tags": 5, "notes": 3, "relationships": 8},
                "schema_info": {"current_version": 5},
            },
            "llm": {
                "status": "healthy",
                "default_model": "gpt-oss:20b",
                "available_models": ["gpt-oss:20b", "mistral:7b"],
                "connectivity_test": {"available": True},
            },
            "system_prompt": {
                "status": "available",
                "prompt_length": 250,
                "prompt_preview": "System prompt content...",
            },
        }

        result = format_debug_output(debug_data)

        # Verify key sections are present
        assert "PRT DEBUG INFORMATION" in result
        assert "SYSTEM ENVIRONMENT" in result
        assert "Darwin 21.6.0 (arm64)" in result
        assert "Python: 3.11.0" in result
        assert "✅ Ollama: ollama version is 0.1.26" in result
        assert "✅ Configuration: Loaded" in result
        assert "✅ Database: Connected" in result
        assert "Contacts: 10" in result
        assert "✅ LLM Service: Available" in result
        assert "Default Model: gpt-oss:20b" in result
        assert "✅ System Prompt: Generated (250 characters)" in result
        assert "✅ Ollama | ✅ Config | ✅ Database | ✅ LLM" in result

    def test_format_debug_output_with_errors(self):
        """Test formatting when components have errors."""
        debug_data = {
            "system_environment": {
                "os": {"system": "Linux", "release": "5.0", "architecture": "x64"},
                "python": {
                    "version": "3.9.0",
                    "implementation": "CPython",
                    "executable": "/usr/bin/python",
                },
                "prt_version": "0.1.0",
                "ollama": {"available": False, "error": "Command not found"},
            },
            "configuration": {"status": "error", "error": "Config file missing"},
            "database": {"status": "error", "error": "Connection failed"},
            "llm": {"status": "error", "error": "Registry unavailable"},
            "system_prompt": {"status": "error", "error": "Cannot generate"},
        }

        result = format_debug_output(debug_data)

        # Verify error states are shown
        assert "❌ Ollama: Not available (Command not found)" in result
        assert "❌ Configuration: Config file missing" in result
        assert "❌ Database: Connection failed" in result
        assert "❌ LLM Service: Registry unavailable" in result
        assert "❌ System Prompt: Cannot generate" in result
        assert "❌ Ollama | ❌ Config | ❌ Database | ❌ LLM" in result


class TestGenerateDebugReport:
    """Test complete debug report generation."""

    @patch("prt_src.debug_info.collect_debug_info")
    @patch("prt_src.debug_info.format_debug_output")
    def test_generate_debug_report_success(self, mock_format, mock_collect):
        """Test successful debug report generation."""
        # Setup mocks
        mock_collect.return_value = {"test": "data"}
        mock_format.return_value = "Formatted output"

        # Test
        result = generate_debug_report()

        # Verify
        mock_collect.assert_called_once()
        mock_format.assert_called_once_with({"test": "data"})
        assert result == "Formatted output"

    @patch("prt_src.debug_info.collect_debug_info")
    def test_generate_debug_report_exception(self, mock_collect):
        """Test debug report generation when an exception occurs."""
        # Setup mock to raise exception
        mock_collect.side_effect = Exception("Collection failed")

        # Test
        result = generate_debug_report()

        # Verify
        assert "Error generating debug report: Collection failed" in result
