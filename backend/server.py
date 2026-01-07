# server.py - Wrapper for modular app structure
# This file exists for backward compatibility with supervisor config
# All code is now organized in app/ directory

from app.main import app

# Re-export app for uvicorn
__all__ = ['app']
