#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_namespace_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'construct',
    'requests',
    'jsonobject',
    'netifaces',
    'hexdump'
]

setup_requirements = [
    'pytest-runner',
]

test_requirements = [
    'pytest>=5',
    'pytest-asyncio'
]

setup(
    author="tuxuser",
    author_email='462620+tuxuser@users.noreply.github.com',
    python_requires='>=3.7',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="Misc durango tools",
    entry_points={
        'console_scripts': [
            'durango-gui=durango.gui.toolbox:main',
            'durango-nwtransfer-client=durango.network_transfer.client:main',
            'durango-nwtransfer-server=durango.network_transfer.server:main',
            'durango-nwtransfer-downloader=durango.network_transfer.store_downloader:main',
            'durango-nand=durango.nand.NANDOne:main',
            'durango-hdd-toggle=durango.hdd.toggle_mode:main',
            'durango-savegame-enum=durango.hdd.savegame_enum:main',
            'durango-extstorage-enum=durango.hdd.external_storage_enum:main',
            'durango-xvd-parser=durango.fileformat.xvd:main'
        ],
    },
    install_requires=requirements,
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='durango',
    name='durango-tools-python',
    packages=find_namespace_packages(include=['durango.*']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/tuxuser/py-durango-tools',
    version='0.1.0',
    zip_safe=False,
)
