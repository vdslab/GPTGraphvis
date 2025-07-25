from setuptools import setup, find_packages

setup(
    name="networkx-mcp",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.103.1",
        "uvicorn>=0.23.2",
        "networkx>=3.1",
        "numpy>=1.25.2",
        "matplotlib>=3.7.2",
        "pydantic>=2.3.0",
        "python-multipart>=0.0.6",
        "requests>=2.31.0",
    ],
    description="NetworkX MCP Server for graph analysis and visualization",
    author="NetworkX MCP Team",
)
