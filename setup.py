from setuptools import find_packages, setup

setup(
    name="experimentation-platform",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.9",
    install_requires=[
        # Base dependencies are read from requirements files
    ],
)
