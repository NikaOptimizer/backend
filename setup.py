from setuptools import setup, find_packages
import os 

setup(
    name=os.path.basename(os.path.dirname(__file__)),  # The name of your package
    version='0.1.0',  # The initial release version
    packages=[
        'nika.backend',
        'nika.backend.api',
        'nika.backend.api.strategies',
        'nika.backend.api.drawings',
        'nika.backend.api.migrations',
        'nika.backend.api.management',
        'nika.backend.api.management.commands',
    ],  # Automatically find package directories
    include_package_data=True, 
    install_requires=[
        # Django owns the HTTP/API bridge between frontend and existing Nika repos.
        'Django>=5.0,<6.0',
        'psycopg[binary]>=3.1.8,<4',
        'data-manager>=0.1.0',
    ],
    author='AZT',
    python_requires='>=3.12',  # Minimum Python version requirement
)
