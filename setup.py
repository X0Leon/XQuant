# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='xquant',
    version='0.5.0',
    description='XQuant Backtest Engine',
    packages=find_packages(exclude=[]),
    author='X0Leon',
    author_email='pku09zl@gmail.com',
    package_data={'': ['*.*']},
    url='https://github.com/X0Leon/XQuant',
    zip_safe=False,
    install_requires=[
        'numpy>=1.11.2'
        'pandas>=0.17.1'
        "matplotlib>=1.5.3",
        "pandas>=0.17.1",
        "scikit-learn>=0.18",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        'Topic :: Software Development :: Libraries :: Python Modules',
        "Operating System :: OS Independent",
        'Programming Language :: Python',
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
    ],
)