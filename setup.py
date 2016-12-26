# -*- coding: utf-8 -*-

import setuptools


setuptools.setup(
    name="xquant",
    version='0.5.1',
    author='Leon Zhang',
    author_email='pku09zl@gmail.com',
    description='Quantitative Backtest Engine',
    keywords='python finance quant',
    url='https://github.com/X0Leon/XQuant',
    license='MIT',
    install_requires=[
        'numpy',
        'pandas',
        'scipy',
        'matplotlib',
        'scikit-learn',
        'requests'
    ],
    packages=['xquant',
              'xquant.engine',
              'xquant.finance',
              'xquant.utils',
              'xquant.visual'],
    long_description='Event-driven backtest frame for Chinese equity/futures market.',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Topic :: Software Development :: Libraries',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
    ]
)
