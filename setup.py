#!/usr/bin/env python3

from setuptools import setup


__version__ = "0.0.0"


setup(name='nodepupper',
      version=__version__,
      description='very good boy',
      url='',
      author='dpedu',
      author_email='dave@davepedu.com',
      packages=['nodepupper'],
      install_requires=[],
      entry_points={
          "console_scripts": [
              "nodepupperd = nodepupper.daemon:main"
          ]
      },
      include_package_data=True,
      package_data={'nodepupper': ['../templates/*.html',
                                   '../templates/fragments/*.html',
                                   '../styles/dist/*']},
      zip_safe=False)
