#!/usr/bin/env python3

from os.path import abspath, dirname, join

from setuptools import setup

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
        'mycroft.intents',
        'mycroft.interfaces',
        'mycroft.interfaces.speech',
        'mycroft.interfaces.speech.recognizers',
        'mycroft.interfaces.speech.stt',
        'mycroft.interfaces.tts',
        'mycroft.services',
        'mycroft.transformers',
        'mycroft.util'
    ],
    install_requires=[
        'PyYAML',
        'pyaml',
        'Twiggy',
        'requests',
        'pocketsphinx',
        'SpeechRecognition',
        'PyAudio',
        'pyserial',
        'pyalsaaudio',
        'tornado',
        'websocket-client',
        'pyinotify',
        'fann2==1.0.7',
        'padatious'
    ],
    entry_points={
        'console_scripts': [
            'mycroft = mycroft.__main__:main'
        ]
    },
    include_package_data=True,
    zip_safe=False
)
