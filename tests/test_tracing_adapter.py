import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import langfuse

from app import tracing


class TracingAdapterTests(unittest.TestCase):
    def test_adapter_uses_the_installed_langfuse_v4_api(self) -> None:
        self.assertEqual(tracing.observe.__module__, langfuse.observe.__module__)
        client = tracing.get_langfuse_client()
        self.assertTrue(callable(client.update_current_span))
        self.assertTrue(callable(client.update_current_generation))
        self.assertTrue(callable(client.start_as_current_observation))

    def test_tracing_is_disabled_without_both_keys(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(tracing.tracing_enabled())

        with patch.dict(os.environ, {"LANGFUSE_PUBLIC_KEY": "pk-only"}, clear=True):
            self.assertFalse(tracing.tracing_enabled())


if __name__ == "__main__":
    unittest.main()
