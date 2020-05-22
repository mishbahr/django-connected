#!/usr/bin/env python


import os
import sys

import connected_accounts

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

version = connected_accounts.__version__

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

if sys.argv[-1] == 'tag':
    print('Tagging the version on github:')
    os.system('git tag -a %s -m "version %s"' % (version, version))
    os.system('git push --tags')
    sys.exit()

readme = open('README.rst').read()

setup(
    name='django-connected',
    version=version,
    description="""Connect your Django powered sites to social networks and other online services.""",
    long_description=readme,
    author='Mishbah Razzaque',
    author_email='mishbahx@gmail.com',
    url='https://github.com/mishbahr/django-connected',
    packages=[
        'connected_accounts',
    ],
    include_package_data=True,
    install_requires=[
        'django-appconf',
        'jsonfield',
        'requests>=1.0',
        'requests_oauthlib>=0.3.0',
    ],
    license="BSD",
    zip_safe=False,
    keywords='django-connected, social auth, oauth, oauth2, facebook, twitter, google',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
)
