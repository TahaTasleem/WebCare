# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['webdirect.py'],
    pathex=[],
    binaries=[],
    datas=[('static', 'static'), ('static/wdres/gclogo.png', 'static'), ('templates', 'templates'), ('webdirect.ini', '.'), ('key.pem', '.'), ('cert.pem', '.'), ('static/wdres/gclogo.ico', 'static')],
    hiddenimports=['engineio.async_drivers.eventlet', 'eventlet.hubs.epolls', 'eventlet.hubs.selects', 'eventlet.hubs.kqueue', 'dns.rdtypes.ANY', 'dns.rdtypes.IN', 'dns.rdtypes.CH', 'dns.rdtypes.dnskeybase', 'dns.asyncbackend', 'dns.dnssec', 'dns.e164', 'dns.namedict', 'dns.tsigkeyring', 'dns.update', 'dns.version', 'dns.zone', 'dns.asyncquery', 'dns.versioned', 'socketserver', 'http.server', 'dns.asyncresolver'],
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
    a.binaries,
    a.datas,
    [],
    name='webdirect',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['static\\wdres\\gclogo.png'],
)
