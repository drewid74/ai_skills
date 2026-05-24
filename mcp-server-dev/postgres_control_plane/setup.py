from setuptools import setup, find_packages

setup(
    name="postgres-control-plane",
    version="0.2.0",
    description="Pluggable task queue (Memory/SQLite/Postgres) with FastMCP server",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "fastmcp>=0.1.0",
    ],
    extras_require={
        "postgres": ["psycopg2-binary>=2.9.0"],
        "dev": ["pytest>=7.0"],
    },
    entry_points={
        "console_scripts": [
            "control-plane=postgres_control_plane.mcp_server:main",
        ],
    },
)
