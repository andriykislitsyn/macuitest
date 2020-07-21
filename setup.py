from distutils.core import setup
from setuptools import find_packages
import subprocess

macos_ver = tuple(int(i) for i in subprocess.getoutput('sw_vers -productVersion').split('.'))


with open('README.md') as fh:
    long_description = fh.read()

setup(
    name='macuitest',
    packages=find_packages(),
    version='0.5.11',
    license='Apache-2.0 License',
    description='A simple UI testing framework for macOS',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Andrii Kislitsyn',
    author_email='andriikislitsyn@gmail.com',
    url='https://github.com/andriykislitsyn',
    download_url='https://github.com/andriykislitsyn/macuitest/archive/v0.5.11-alpha.tar.gz',
    keywords=['Testing', 'UI', 'Functional', 'macOS'],
    install_requires=[
        'biplist',
        'opencv-python == 3.4.8.29' if macos_ver < (10, 13) else 'opencv-python',
        'pillow',
        'pyobjc-framework-ApplicationServices',
        'pyobjc-framework-Cocoa',
        'pyobjc-framework-CoreText',
        'pyobjc-framework-Quartz',
        'PyTweening',
        'webcolors',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Topic :: Software Development :: Testing',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Education :: Testing',
        'Operating System :: MacOS',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
)
