from distutils.core import setup
from setuptools import find_packages

setup(
    name='macuitest',
    packages=find_packages(),
    version='0.5.2',
    license='Apache-2.0 License',
    description='A simple UI testing framework for macOS',
    author='Andrii Kislitsyn',
    author_email='andriikislitsyn@gmail.com',
    url='https://github.com/andriykislitsyn',
    download_url='https://github.com/andriykislitsyn/macuitest/archive/v0.5.2-alpha.tar.gz',
    keywords=['Testing', 'UI', 'Functional', 'macOS'],
    install_requires=[
        'biplist',
        'mss',
        'opencv-python',
        'pillow',
        'pyobjc-framework-ApplicationServices',
        'pyobjc-framework-Cocoa',
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
