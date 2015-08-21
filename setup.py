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
    },

    # Metadata
    author='Devin Ekins',
    author_email='devinj.ekins@gmail.com',
    description='Linter that will examine only new changes as you commit them',
    license='GPLv2',
    keywords='linter lint git commit hook node js',
    url='https://github.com/endlessm/difflint')
