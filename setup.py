from setuptools import setup, find_packages

setup(
    name="dsca-data-explorer",
    version="1.0.0",
    description="Multi-source geospatial/environmental data explorer for DSCA, emergency management, and research.",
    author="Your Name",
    author_email="your.email@yourdomain.com",
    packages=find_packages(),
    install_requires=[
        "requests",
        "pandas",
        "openpyxl",
        "python-docx",
        "reportlab",
        "urllib3"
    ],
    entry_points={
        "console_scripts": [
            "dsca-explorer = dsca_explorer.gui:run_gui"
        ]
    },
    include_package_data=True,
    license="MIT",
    python_requires=">=3.8",
)
