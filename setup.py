# -*- coding: utf-8 -*-


import re
import ast
import os

from setuptools import setup, find_packages


_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('wechat/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')
    ).group(1)))


def fread(fname):
    filepath = os.path.join(os.path.dirname(__file__), fname)
    if os.path.exists(filepath):
        with open(filepath) as f:
            return f.read()


setup(
    name='python-wechat',
    description='Wechat for Python',
    long_description=fread('docs/quickstart.rst'),
    license='BSD',
    packages=find_packages(),
    version=version,
    author='zwczou',
    author_email='zwczou@gmail.com',
    maintainer='catroll',
    maintainer_email='ninedoors@126.com',
    url='https://github.com/catroll/python-wechat',
    keywords=['wechat', 'wechat pay', 'wechat login', 'wechat mp', 'wechat python'],
    zip_safe=False,
    platforms='any',
    install_requires=[
        'requests',
        'lxml',
    ],
    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
    ],
)
