from setuptools import setup, find_packages

setup(
    name="social-app-scraper",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests",
        "beautifulsoup4",
        "google-generativeai",
    ],
    python_requires=">=3.7",
) 