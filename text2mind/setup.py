from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = f.read().splitlines()

setup(
    name="text2mind",
    version="0.1.0",
    author="Author",
    author_email="author@example.com",
    description="A tool to convert text to XMind mind maps and export them as PNG images",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/text2mind",
    packages=find_packages(),
    package_dir={"": "src"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "text2mind=main:cli",
        ],
    },
) 