# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ["src/smk/core/desktop/__main__.py"],
    pathex=[],
    binaries=[],
    datas=[  # codespell:ignore datas
        ("src/smk/core/web/templates", "smk/core/web/templates"),
        ("src/smk/core/web/static", "smk/core/web/static"),
    ],
    hiddenimports=[
        "uvicorn.logging",
        "uvicorn.loops.auto",
        "uvicorn.loops.asyncio",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.http.h11_impl",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan.on",
        "uvicorn.lifespan.off",
        "smk.core.web.routes.api",
        "smk.core.web.routes.pages",
        "smk.core.web.routes.partials",
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
    name="SMK",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,  # codespell:ignore datas
    strip=False,
    upx=True,
    upx_exclude=[],
    name="SMK",
)

app = BUNDLE(
    coll,
    name="SMK.app",
    icon=None,
    bundle_identifier="io.spacelift.smk",
)
