"""
AIWindows Client Version
========================
Windows-Version des AILinux Desktop Clients
"""

VERSION = "1.0.0"
BUILD_DATE = "20251217"
PLATFORM = "windows"

CHANGELOG = """
# AIWindows Client Changelog

## Version 1.0.0 (2025-12-17)

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
