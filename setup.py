from setuptools import setup, find_packages

setup(
    name='pyternity',
    version='1.0.0',
    description='Calculate modernity signatures for PyPI projects',
    packages=find_packages(),
    install_requires=[
        "vermin==1.5.1",
        "matplotlib==3.6.2",
        "Sphinx==4.5.0"
    ],
    python_requires=">=3.11",
    include_package_data=True
)
