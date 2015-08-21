from setuptools import setup, find_packages

setup(name='difflint', version='0.0.0',
    packages=find_packages(),
    package_data={
        'difflint': ['data/*'],
    },

    entry_points={
        'console_scripts': [
            'difflint = difflint:main',
        ],
    })
