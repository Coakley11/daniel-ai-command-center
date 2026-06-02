"""Secrets resolution for Supabase (Streamlit SecretsDict-compatible)."""

from __future__ import annotations

import os
import unittest
from types import SimpleNamespace

from suite_storage_config import (
    EXPECTED_SECRETS_TOML,
    _mapping_get,
    get_cloud_config,
    reset_cloud_config_cache,
)


class _SecretsSection:
    """Mimics Streamlit secrets section (has .get and attributes, not always dict)."""

    def __init__(self, **kwargs: str) -> None:
        self._data = kwargs

    def get(self, key: str, default: str | None = None) -> str | None:
        return self._data.get(key, default)

    def __getattr__(self, name: str) -> str:
        return self._data[name]


class TestSuiteStorageConfig(unittest.TestCase):
    def tearDown(self) -> None:
        reset_cloud_config_cache()
        os.environ.pop("SUITE_SUPABASE_URL", None)
        os.environ.pop("SUITE_SUPABASE_KEY", None)

    def test_mapping_get_on_secrets_section(self) -> None:
        block = _SecretsSection(
            supabase_url="https://abc.supabase.co",
            supabase_key="secret",
        )
        self.assertEqual(_mapping_get(block, "supabase_url"), "https://abc.supabase.co")
        self.assertEqual(_mapping_get(block, "supabase_key"), "secret")

    def test_expected_toml_has_section(self) -> None:
        self.assertIn("[suite_activity]", EXPECTED_SECRETS_TOML)
        self.assertIn("supabase_url", EXPECTED_SECRETS_TOML)
        self.assertIn("supabase_key", EXPECTED_SECRETS_TOML)

    def test_env_vars_resolve(self) -> None:
        os.environ["SUITE_SUPABASE_URL"] = "https://test.supabase.co"
        os.environ["SUITE_SUPABASE_KEY"] = "key123"
        cfg = get_cloud_config()
        self.assertIsNotNone(cfg)
        assert cfg is not None
        self.assertEqual(cfg.url, "https://test.supabase.co")


if __name__ == "__main__":
    unittest.main()
