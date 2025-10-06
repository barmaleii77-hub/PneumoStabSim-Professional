#!/usr/bin/env python3
"""
Setup script для PneumoStabSim
"""
from setuptools import setup, find_packages
from pathlib import Path

# Читаем README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Читаем requirements
requirements = []
requirements_file = this_directory / "requirements.txt"
if requirements_file.exists():
    requirements = requirements_file.read_text().strip().split('\n')

setup(
    name="pneumostabsim",
    version="2.0.0",
    author="barmaleii77-hub",
    author_email="",
    description="Pneumatic Stabilizer Simulator with interactive 3D interface",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/barmaleii77-hub/NewRepo2",
    
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Education", 
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.13",
        "Topic :: Scientific/Engineering :: Physics",
        "Topic :: Scientific/Engineering :: Visualization",
    ],
    
    python_requires=">=3.13",
    install_requires=requirements,
    
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-qt>=4.0.0", 
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
    },
    
    entry_points={
        "console_scripts": [
            "pneumostabsim=app:main",
        ],
    },
    
    include_package_data=True,
    package_data={
        "": ["*.qml", "*.yaml", "*.css", "*.svg", "*.png", "*.ico"],
    },
    
    zip_safe=False,
    
    project_urls={
        "Bug Reports": "https://github.com/barmaleii77-hub/NewRepo2/issues",
        "Source": "https://github.com/barmaleii77-hub/NewRepo2",
        "Documentation": "https://github.com/barmaleii77-hub/NewRepo2/docs",
    },
)
