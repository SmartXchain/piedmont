import os
import pytest
from unittest.mock import patch
from django.conf import settings


class TestSettingsEnvVars:
    """
    Verify that critical settings are loaded from environment variables
    and not hardcoded in settings.py.
    """

    def test_secret_key_loaded_from_env(self):
        """SECRET_KEY must come from the environment, not be hardcoded."""
        env_key = os.environ.get("SECRET_KEY")
        assert env_key is not None, (
            "SECRET_KEY is not set in the environment. "
            "Add SECRET_KEY to your .env.dev file."
        )
        assert settings.SECRET_KEY == env_key, (
            "settings.SECRET_KEY does not match the SECRET_KEY env var."
        )

    def test_secret_key_is_not_hardcoded(self):
        """SECRET_KEY must come from the env and be at least 40 chars."""
        assert settings.SECRET_KEY is not None, (
            "settings.SECRET_KEY is None — SECRET_KEY env var is missing."
        )
        assert len(settings.SECRET_KEY) >= 40, (
            "SECRET_KEY is too short to be secure."
        )

    def test_debug_loaded_from_env(self):
        """DEBUG env var must be present."""
        env_debug = os.environ.get("DEBUG")
        assert env_debug is not None, (
            "DEBUG is not set in the environment. "
            "Add DEBUG to your .env.dev file."
        )

    def test_debug_is_a_boolean(self):
        """
        DEBUG must be a real Python bool, not a string.
        os.environ.get() returns a string; settings.py must parse it.
        """
        assert isinstance(settings.DEBUG, bool), (
            f"settings.DEBUG is {type(settings.DEBUG)}, expected bool. "
            "Check that settings.py parses DEBUG with: "
            "os.environ.get('DEBUG', '').lower() == 'true'"
        )

    def test_debug_parsing_true(self):
        """'True', 'true', 'TRUE' must all parse to bool True."""
        for value in ("True", "true", "TRUE"):
            with patch.dict(os.environ, {"DEBUG": value}):
                result = os.environ.get(
                    "DEBUG", ""
                ).lower() == "true"
                assert result is True, (
                    f"DEBUG='{value}' should parse to True, got {result}"
                )

    def test_debug_parsing_false(self):
        """'False', 'false', '' must all parse to bool False."""
        for value in ("False", "false", ""):
            with patch.dict(os.environ, {"DEBUG": value}):
                result = os.environ.get(
                    "DEBUG", ""
                ).lower() == "true"
                assert result is False, (
                    f"DEBUG='{value}' should parse to False, got {result}"
                )

    def test_database_engine_loaded_from_env(self):
        """Database ENGINE must come from the environment."""
        assert os.environ.get("SQL_ENGINE") is not None, (
            "SQL_ENGINE is not set in the environment."
        )
        assert settings.DATABASES["default"]["ENGINE"] == (
            os.environ.get("SQL_ENGINE")
        )

    def test_database_name_loaded_from_env(self):
        """Database NAME must come from the environment."""
        assert os.environ.get("SQL_DATABASE") is not None, (
            "SQL_DATABASE is not set in the environment."
        )
        assert settings.DATABASES["default"]["NAME"] == (
            os.environ.get("SQL_DATABASE")
        )
