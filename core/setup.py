
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(name='Mycroft Core Aliases',
      version='0.1.0',
      description='Aliases for objects in Mycroft Light',
      author='Mycroft AI',
      author_email='support@mycroft.ai',
      maintainer='Matthew Scholefield',
      maintainer_email='matthew.scholefield@mycroft.ai',
      url='https://github.com/matthewscholefield/mycroft-light',
      py_modules=['mycroft_core'],
      license='Apache-2',
      install_requires=['mycroft-light'],
     )