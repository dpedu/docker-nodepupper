#!/usr/bin/env python3

from setuptools import setup
import os


__version__ = "0.0.2"
with open(os.path.join(os.path.dirname(__file__), "requirements.txt")) as f:
    __requirements__ = [line.strip() for line in f.readlines()]


setup(name='nodepupper',
      version=__version__,
      description='very good boy',
      url='',
      author='dpedu',
      author_email='dave@davepedu.com',
      packages=['nodepupper'],
      install_requires=__requirements__,
      entry_points={
          "console_scripts": [
              "nodepupperd = nodepupper.daemon:main",
              "npcli = nodepupper.cli:main"
          ]
      },
      include_package_data=True,
      package_data={'nodepupper': ['../templates/*.html',
                                   '../templates/fragments/*.html',
                                   '../styles/dist/*']},
      zip_safe=False)
