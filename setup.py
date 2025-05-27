from setuptools import setup

APP = ['run_explorer.py']
DATA_FILES = [
    ('dsca_explorer/templates', ['dsca_explorer/templates/export_template.html']),
    ('dsca_explorer/static', ['dsca_explorer/static/style.css'])
]
OPTIONS = {
    'argv_emulation': True,
    'plist': {
        'CFBundleName': "DSCA Data Explorer",
        'CFBundleShortVersionString': "1.0.0",
        'NSHumanReadableCopyright': "Copyright © 2023, Your Name"
    }
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
