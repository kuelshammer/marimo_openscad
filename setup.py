"""
Setup script for marimo-openscad package
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="marimo-openscad",
    version="1.0.0",
    author="Marimo-OpenSCAD Contributors",
    author_email="",
    description="Interactive 3D CAD modeling in Marimo notebooks using SolidPython2 and OpenSCAD",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/marimo-openscad",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Multimedia :: Graphics :: 3D Modeling",
    ],
    python_requires=">=3.8",
    install_requires=[
        "marimo>=0.13.0",
        "solidpython2>=1.0.0",
        "anywidget>=0.9.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov",
            "black",
            "isort",
            "mypy",
        ],
    },
    keywords=[
        "marimo",
        "openscad",
        "3d",
        "cad",
        "modeling",
        "solidpython2",
        "jupyter",
        "notebook",
        "reactive",
        "webgl",
        "three.js",
    ],
    project_urls={
        "Bug Reports": "https://github.com/your-username/marimo-openscad/issues",
        "Source": "https://github.com/your-username/marimo-openscad",
        "Documentation": "https://github.com/your-username/marimo-openscad/blob/main/docs/",
    },
)