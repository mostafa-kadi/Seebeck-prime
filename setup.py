from setuptools import setup, find_packages

setup(
    name="seebeck-prime",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    author="Seebeck Prime Development Team",
    author_email="development@seebeck-prime.com",
    description="A comprehensive platform for thermoelectric materials analysis.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/user/seebeck-prime",  # Replace with your repo URL
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",  # Or your chosen license
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=["numpy", "pandas", "scipy", "matplotlib", "pyqt6", "pytz"],
    extras_require={"dev": ["pytest", "pytest-cov", "black", "ruff", "mypy"]},
)
