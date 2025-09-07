from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="code-change-analyzer",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="一个基于Python和AI的代码变更分析与测试通知系统",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.example.com/project/code-change-analyzer",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "code-change-analyzer=main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)