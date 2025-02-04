# setup.py
"""
Usage:
    python setup.py py2app

This will create a .app in 'dist/' that you can distribute.
"""

from setuptools import setup

APP = ['app.py']  # Your main script that starts Flask
DATA_FILES = [
    ('templates', ['templates/index.html',
                   'templates/pick_brand.html',
                   'templates/pick_models.html',
                   'templates/results.html'])
]
OPTIONS = {
    # "argv_emulation": True,        # If you had a GUI that needs cmdline arguments
    # "iconfile": "my_icon.icns",    # If you have a custom .icns icon
    # "packages": ["flask", "requests", ...], # Not always needed, but can help if py2app doesn't auto-detect them
    "includes": [
        "fuzzy_match",     # Force py2app to include your modules if auto-discovery misses them
        "otoparts_dict",
        "autopia_dict"
    ],
    "resources": [
        # Another way to ensure your entire 'templates' folder is included
        # or other data you might need
    ],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
