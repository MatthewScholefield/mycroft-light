#!/usr/bin/env python3

from setuptools import setup

from os.path import abspath, dirname, join

with open(join(abspath(dirname(__file__)), 'requirements.txt')) as f:
    requirements = [i for i in f.readlines() if not i.strip().startswith('#')]

setup(
    name='mycroft-light',
    version='0.1.0',
    description='A redesigned Mycroft implementation',
    url='http://github.com/MatthewScholefield/mycroft-light',
    author='Mycroft AI Inc.',
    author_email='support@mycroft.ai',
    maintainer='Matthew D. Scholefield',
    maintainer_email='matthew.scholefield@mycroft.ai',	
    license='Apache-2.0',
    packages=[
        'mycroft',
        'mycroft.clients',
        'mycroft.clients.speech',
        'mycroft.clients.speech.recognizers',
        'mycroft.clients.speech.tts',
        'mycroft.engines',
        'mycroft.formats',
        'mycroft.managers',
        'mycroft.parsing',
        'mycroft.parsing.en_us',
        'mycroft.util'
    ],
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'mycroft = mycroft.__main__:main'
        ]
    },
    include_package_data=True,
    zip_safe=False
)
