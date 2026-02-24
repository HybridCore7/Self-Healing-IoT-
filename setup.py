"""
Setup configuration for Self-Healing IoT System
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="self-healing-iot",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="AI-Enabled Self-Healing IoT System for Autonomous Fault Detection and Recovery",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/self-healing-iot",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=[
        "fastapi>=0.104.1",
        "uvicorn[standard]>=0.24.0",
        "pydantic>=2.5.0",
        "pydantic-settings>=2.1.0",
        "paho-mqtt>=1.6.1",
        "scikit-learn>=1.3.2",
        "numpy>=1.24.3",
        "pandas>=2.1.3",
        "aiosqlite>=0.19.0",
        "streamlit>=1.28.2",
        "plotly>=5.18.0",
        "python-dotenv>=1.0.0",
        "pyyaml>=6.0.1",
        "loguru>=0.7.2",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "pytest-cov>=4.1.0",
            "black>=23.11.0",
            "flake8>=6.1.0",
            "mypy>=1.7.1",
        ],
    },
    entry_points={
        "console_scripts": [
            "iot-backend=backend.main:main",
            "iot-simulator=simulator.device_simulator:main",
        ],
    },
)
