from setuptools import setup

APP = ['run_explorer.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'site_packages': True,
    'packages': [],
    'includes': [],
    'excludes': [],
    'resources': [],
    'plist': {
        'CFBundleName': 'DSCA Data Explorer',
        'CFBundleDisplayName': 'DSCA Data Explorer',
        'CFBundleGetInfoString': 'A modern Python tool for geospatial data exploration',
        'CFBundleIdentifier': 'com.djdev.dscadataexplorer',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True,
    }
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
