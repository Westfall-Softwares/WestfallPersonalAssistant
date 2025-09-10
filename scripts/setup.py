from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="westfall-assistant",
    version="2.0.0",
    author="Westfall Softwares",
    author_email="contact@westfallsoftwares.com",
    description="A secure, AI-powered entrepreneur assistant with Tailor Pack extensions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Westfall-Softwares/WestfallPersonalAssistant",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Office/Business :: Entrepreneur Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "westfall-assistant=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.json"],
        "data": ["*.db"],
        "assets": ["*.png", "*.jpg", "*.ico"],
    },
)