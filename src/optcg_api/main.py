#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/26 14:48:29.996145
Revised: 2026/03/26 14:48:29.996145
"""

import uvicorn

from optcg_api.app import app  # noqa: F401


def main():
    uvicorn.run("optcg_api.app:app", host="0.0.0.0", port=8000, reload=True)
