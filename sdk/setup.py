from setuptools import setup, find_packages

setup(
    name="parceldata",
    version="0.1.0",
    description="ParcelData Python SDK — Real estate data for AI agents",
    long_description=open("../README.md").read(),
    long_description_content_type="text/markdown",
    author="Dharma Technologies, Inc.",
    author_email="hello@dharma.tech",
    url="https://parceldata.ai",
    project_urls={
        "Documentation": "https://docs.parceldata.ai",
        "Source": "https://github.com/Dharma-Technologies/parceldata",
        "Issues": "https://github.com/Dharma-Technologies/parceldata/issues",
    },
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "httpx>=0.26.0",
        "pydantic>=2.5.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.23.0",
            "mypy>=1.8.0",
            "ruff>=0.1.0",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="real-estate property-data api mcp ai-agents",
    license="MIT",
)
