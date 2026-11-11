"""
AIWindows Client Version
========================
Windows-Version des AILinux Desktop Clients
"""

VERSION = "1.0.2"
BUILD_DATE = "20261111"
PLATFORM = "windows"

CHANGELOG = """
# AIWindows Client Changelog

## Version 1.0.2 (2026-11-11)

### Patch
- Python dependency patches: aiohttp 3.14.5, pydantic 2.14.3 and anyio 4.16.0.
- Update websockets minimum to 17.3 and pywinpty minimum to 3.1.0.
- Synchronize UI, installer and MCP client version reporting.

## Version 1.0.1 (2026-09-11)

### Neu
- Erste Windows-Version
- PowerShell Terminal Integration
- Windows File Browser mit Laufwerks-Support
- AI Chat (identisch mit Linux-Version)
- Web Browser Integration
- Auto-Update System

### Features
- Tier-System (Free/Pro) wie Linux
- Ollama Integration
- Cloud-Modelle (Claude, Gemini, GPT)
- MCP Node Support
"""

# Windows-spezifische Pfade
import os
DEFAULT_HOME = os.path.expanduser("~")
DEFAULT_SHELL = "powershell.exe"
