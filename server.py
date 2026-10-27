"""Solvero DistroKid MCP: prepare and validate release metadata, without uploading releases."""
import json
import os
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

PUBLIC_HOST = os.environ.get("SOLVERO_PUBLIC_HOST", "solvero-distrokid-mcp.onrender.com")
app = FastMCP(
    "Solvero DistroKid",
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=[PUBLIC_HOST, f"{PUBLIC_HOST}:*", "localhost:*", "127.0.0.1:*"],
        allowed_origins=["https://chatgpt.com"],
    ),
)
DATA_DIR = Path(os.environ.get("SOLVERO_DATA_DIR", "./data")).resolve()

def validate(title: str, artist: str, audio_path: str, cover_path: str) -> dict:
    errors = []
    if not title.strip(): errors.append("Missing release title")
    if not artist.strip(): errors.append("Missing artist")
    if not audio_path.strip(): errors.append("Missing audio file path")
    elif not Path(audio_path).is_file(): errors.append("Audio file not found")
    if not cover_path.strip(): errors.append("Missing cover file path")
    elif not Path(cover_path).is_file(): errors.append("Cover file not found")
    return {"valid": not errors, "errors": errors}

@app.tool()
def validate_release(title: str, artist: str, audio_path: str, cover_path: str) -> dict:
    """Check metadata presence and local file existence (not DistroKid's full requirements)."""
    return validate(title, artist, audio_path, cover_path)

@app.tool()
def prepare_release(title: str, artist: str, audio_path: str, cover_path: str,
                    genre: str = "", release_date: str = "", lyrics: str = "") -> dict:
    """Build a local release manifest; never uploads or publishes."""
    check = validate(title, artist, audio_path, cover_path)
    return {"release": {"title": title.strip(), "artist": artist.strip(), "audio_path": audio_path,
            "cover_path": cover_path, "genre": genre, "release_date": release_date, "lyrics": lyrics},
            "check": check, "publication_status": "not_submitted"}

@app.tool()
def save_release_manifest(title: str, artist: str, audio_path: str, cover_path: str,
                          genre: str = "", release_date: str = "") -> dict:
    """Write a JSON manifest into the configured data directory; no DistroKid API calls."""
    package = prepare_release(title, artist, audio_path, cover_path, genre, release_date)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / "release-manifest.json"
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(package, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)
    return {"path": str(path), **package}

if __name__ == "__main__":
    app.run(transport="stdio")
