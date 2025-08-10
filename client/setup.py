"""Setup script for plomtts-client."""

from setuptools import find_packages, setup

setup(
    name="plomtts-client",
    version="1.0.0",
    author="Avalon Parton",
    author_email="avalonlee@gmail.com",
    description="Python client for PlomTTS AI Text-to-Speech server",
    url="https://github.com/plomdawg/plomtts",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.31.0",
        "pydantic>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-mock>=3.10.0",
            "responses>=0.23.0",
            "black>=23.0.0",
            "isort>=5.12.0",
        ],
    },
)
