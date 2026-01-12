# setup.py
from setuptools import setup, find_packages

setup(
    name="mispred-analyzer",
    version="1.0.0",
    author="hsp",
    description="Analyze PC misprediction statistics from CondTrace tables",
    packages=find_packages(),
    install_requires=[
        "flask>=2.0.0",
        "matplotlib>=3.5.0",
        "numpy>=1.21.0",
    ],
    entry_points={
        "console_scripts": [
            "mispred-analyzer=mispred_analyzer.main:main",
        ],
    },
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)