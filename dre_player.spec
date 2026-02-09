# dre_player.spec
import os
import sounddevice

block_cipher = None

# Path to sounddevice's internal data (PortAudio DLLs)
sd_path = os.path.dirname(sounddevice.__file__)
sd_data_path = os.path.join(sd_path, '_sounddevice_data')

a = Analysis(
    ['gui_player.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets/icon.ico', 'assets'),
        ('core', 'core'),
        (sd_data_path, '_sounddevice_data'),
    ],
    hiddenimports=[
        'core.hybrid.pipeline',
        'sounddevice',
        'numpy',
        'soundfile',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.QtCore',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PyQt6.QtMultimedia',
        'PyQt6.QtMultimediaWidgets',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='DigitalReverseEnginePlayer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='assets/icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DigitalReverseEnginePlayer',
)
