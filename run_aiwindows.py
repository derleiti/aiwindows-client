#!/usr/bin/env python3
"""Frozen-app entry point that preserves aiwindows_client as a package."""
import sys
from aiwindows_client.main import main

if __name__ == "__main__":
    raise SystemExit(main())
