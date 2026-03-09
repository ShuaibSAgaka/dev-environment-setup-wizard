from setuptools import setup, find_packages

setup(
    name="dev-wizard",
    version="1.0.0",
    description="Interactive Dev Environment Setup Wizard — Node.js + npm on WSL/Ubuntu",
    author="Shuaib S. Agaka",
    python_requires=">=3.9",
    packages=find_packages(),
    install_requires=["rich>=13.7.0"],
    entry_points={
        "console_scripts": [
            "devwizard=devwizard.wizard:run_wizard",
        ]
    },
)