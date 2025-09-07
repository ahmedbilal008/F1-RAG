"""
Setup script for F1 RAG Chatbot
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="f1-rag-chatbot",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A Formula 1 RAG Chatbot using Pinecone and Google Gemini AI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/f1-rag-chatbot",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    include_package_data=True,
    package_data={
        "src": ["data/*.json"],
        "static": ["css/*.css"],
    },
)