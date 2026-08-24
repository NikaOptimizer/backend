from setuptools import setup, find_packages
import os 

setup(
    name=os.path.basename(os.path.dirname(__file__)),  # The name of your package
    version='0.1.0',  # The initial release version
    packages=[
        'nika.backend',
        'nika.backend.api',
        'nika.backend.api.strategies',
    ],  # Automatically find package directories
    include_package_data=True, 
    install_requires=[
        # Django owns the HTTP/API bridge between frontend and existing Nika repos.
        'Django>=5.0,<6.0',
    ],
    author='AZT',
    python_requires='>=3.12',  # Minimum Python version requirement
)
