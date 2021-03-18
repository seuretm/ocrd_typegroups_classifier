# -*- coding: utf-8 -*-
import codecs

from setuptools import setup, find_packages

with codecs.open('README.md', encoding='utf-8') as f:
    README = f.read()

setup(
    name='ocrd_typegroups_classifier',
    version='0.0.1',
    description='Typegroups classifier for OCR',
    long_description=README,
    long_description_content_type='text/markdown',
    author='Matthias Seuret, Konstantin Baierer',
    author_email='seuretm@users.noreply.github.com',
    url='https://github.com/seuretm/ocrd_typegroups_classifier',
    license='Apache License 2.0',
    packages=find_packages(exclude=('tests', 'docs')),
    include_package_data=True,
    install_requires=[
        'click',
        'ocrd >= 2.0.2',
        'pandas',
        'Pillow == 8.1.1',
        'scikit-image',
        'torch >= 1.3.1',
        'torchvision',
    ],
    package_data={
        '': ['*.json', '*.tgc'],
    },
    entry_points={
        'console_scripts': [
            'typegroups-classifier=ocrd_typegroups_classifier.cli.simple:cli',
            'ocrd-typegroups-classifier=ocrd_typegroups_classifier.cli.ocrd_cli:cli',
        ]
    },
)
