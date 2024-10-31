from setuptools import setup, find_packages

setup(
    name="gopro-synapse",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        'open-gopro',
        'rich',
        'typing-extensions',
        'bleak',
    ],
    entry_points={
        'console_scripts': [
            'gosynapse=gosynapse.scripts.gosynapse_cli:main',
        ],
    },
    include_package_data=True,
    package_data={
        'gosynapse': ['config/*.ini'],
    },
    author="Armand du Plessis",
    author_email="adp@livelabs.ventures",
    description="A GoPro livestreaming service for Raspberry Pi",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/armanddp/synapse",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires='>=3.7',
)
