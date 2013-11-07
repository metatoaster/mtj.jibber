from setuptools import setup, find_packages
import os

version = '0.1'

long_description = (
    open('README.rst').read() + '\n' +
    open('CHANGES.rst').read() + '\n'
    )

setup(name='mtj.jibber',
      version=version,
      description="A jabber bot",
      long_description=long_description,
      # Get more strings from
      # http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Programming Language :: Python",
        ],
      keywords='',
      author='Tommy Yu',
      author_email='y@metatoaster.com',
      url='https://github.com/metatoaster/mtj.jibber/',
      license='gpl',
      packages=find_packages(),
      namespace_packages=['mtj'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          # -*- Extra requirements: -*-
          'sleekxmpp',
      ],
      entry_points="""
      # -*- Entry points: -*-
      [console_scripts]
      jibber = mtj.jibber.ctrl:main
      """,
      )
