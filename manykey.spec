# -*- mode: python -*-

block_cipher = None


a = Analysis(['manykey.py'],
             pathex=['/Users/evan/Code/Python/manykey_writer'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='manykey',
          debug=False,
          strip=False,
          upx=True,
          console=False )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='manykey')
app = BUNDLE(coll,
             name='ManyKey Writer.app',
             icon='manykeysquare.icns',
             bundle_identifier=None,
             info_plist={'NSHighResolutionCapable': 'True'})
