"""Offline tests: stub MCP decorator; no external account/API needed."""
import importlib.util
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

fake_mcp = types.ModuleType("mcp")
fake_server = types.ModuleType("mcp.server")
fake_fastmcp = types.ModuleType("mcp.server.fastmcp")
class FastMCP:
    def __init__(self, name): self.name = name
    def tool(self): return lambda fn: fn
fake_fastmcp.FastMCP = FastMCP
fake_server.fastmcp = fake_fastmcp
fake_mcp.server = fake_server
sys.modules.update({"mcp": fake_mcp, "mcp.server": fake_server, "mcp.server.fastmcp": fake_fastmcp})
spec = importlib.util.spec_from_file_location("server_under_test", Path(__file__).resolve().parents[1] / "server.py")
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)

class OfflineTests(unittest.TestCase):
    def test_tools_exist(self):
        for name in ["validate_release","prepare_release","save_release_manifest"]:
            self.assertTrue(callable(getattr(server, name)))
    def test_missing_files(self):
        result = server.validate_release("Single", "Solvero", "/not/found.wav", "/not/found.png")
        self.assertFalse(result["valid"])
        self.assertEqual(len(result["errors"]), 2)
    def test_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            with patch.object(server, "DATA_DIR", Path(d)):
                audio = Path(d) / "song.wav"
                cover = Path(d) / "cover.png"
                audio.write_bytes(b"audio")
                cover.write_bytes(b"image")
                result = server.save_release_manifest("Single", "Solvero", str(audio), str(cover))
                self.assertTrue(result["check"]["valid"])
                self.assertEqual(result["publication_status"], "not_submitted")
                self.assertTrue((Path(d) / "release-manifest.json").exists())

if __name__ == "__main__":
    unittest.main()
