from setuptools import setup, find_packages

setup(
    name="networkxmcp",
    version="1.0.0",
    description="NetworkX MCP Server for network visualization and analysis",
    packages=["layouts", "metrics", "tools"],
    python_requires=">=3.12",
    install_requires=[
        "fastapi>=0.95.0",
        "uvicorn>=0.21.1",
        "networkx>=3.0",
        "numpy>=1.24.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "matplotlib>=3.7.0",
        "scikit-learn>=1.2.0",
        "python-louvain>=0.16",
        "fastapi-mcp==0.3.7"
    ],
)
