# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec file for SMK desktop application
#
# Plugin System Notes:
# - Built-in plugins are bundled from src/smk/plugins/
# - Third-party plugins load from ~/.config/smk/plugins/ (not bundled)
# - Plugin dependencies auto-install to ~/.config/smk/plugin-deps/ at runtime
# - pip is automatically bundled with Python for runtime installation
# - Common dependencies (boto3, requests) can be pre-bundled to reduce runtime installs
#

import sys

# Platform-specific icon selection
# Icons generated from scripts/build-icons.sh
if sys.platform == 'darwin':
    ICON_PATH = 'src/smk/core/desktop/assets/icon.icns'
elif sys.platform == 'win32':
    ICON_PATH = 'src/smk/core/desktop/assets/icon.ico'
else:  # Linux and others
    ICON_PATH = 'src/smk/core/desktop/assets/icon.png'

a = Analysis(
    ["src/smk/core/desktop/__main__.py"],
    pathex=[],
    binaries=[],
    datas=[  # codespell:ignore datas
        ("src/smk/core/web/templates", "smk/core/web/templates"),
        ("src/smk/core/web/static", "smk/core/web/static"),
        ("src/smk/plugins", "smk/plugins"),  # Built-in plugins
    ],
    hiddenimports=[
        # Desktop wrapper
        "webview",
        # Uvicorn server dependencies
        "uvicorn.logging",
        "uvicorn.loops.auto",
        "uvicorn.loops.asyncio",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.http.h11_impl",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan.on",
        "uvicorn.lifespan.off",
        # Web routes
        "smk.core.web.routes.api",
        "smk.core.web.routes.workflow",
        "smk.core.web.routes.partials",
        # Plugin system
        "pluggy",
        "importlib.util",
        "importlib.machinery",
        "smk.core.plugins",
        "smk.core.plugins.manager",
        "smk.core.plugins.loader",
        "smk.core.plugins.dependencies",
        "smk.core.plugins.hooks",
        "smk.core.plugins.cache",
        # Common plugin dependencies (pre-bundled to reduce runtime installation)
        # Add these to pyproject.toml dependencies if not already present:
        # "boto3>=1.35",      # AWS operations
        # "requests>=2.32",   # HTTP clients
        # "pyyaml>=6.0",      # Config parsing (already included)
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Spacelift-Migration-Kit",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=ICON_PATH,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,  # codespell:ignore datas
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Spacelift-Migration-Kit",
)

app = BUNDLE(
    coll,
    name="Spacelift Migration Kit.app",
    icon=ICON_PATH,
    bundle_identifier="io.spacelift.smk",
)
