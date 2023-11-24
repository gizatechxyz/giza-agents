from setuptools import setup, find_packages

setup(
    name="giza-sdk",
    version="0.1.0",
    description="A Python SDK for Giza platform",
    author="Your Name",
    author_email="your.email@example.com",
    license="MIT",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.21.2",
        "pandas>=1.3.2",
        "prefect>=0.15.4",
        "onnx>=1.10.1",
    ],
    extras_require={
        "dev": ["pytest>=6.2.5"]
    },
    entry_points={
        "console_scripts": [
            "giza=giza.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
    ],
    python_requires='>=3.8',
)
