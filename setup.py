from distutils.core import setup
from setuptools import find_packages

setup(
    name='macuitest',
    packages=find_packages(),
    version='0.5',
    license='Apache-2.0 License',
    description='A simple UI testing framework for macOS',
    author='Andrii Kislitsyn',
    author_email='andriikislitsyn@gmail.com',
    url='https://github.com/andriykislitsyn',
    download_url='https://github.com/andriykislitsyn/macuitest/archive/v0.5-alpha.tar.gz',
    keywords=['Testing', 'UI', 'Functional', 'macOS'],
    install_requires=[
        'biplist',
        'mss',
        'opencv-python',
        'pyobjc-core',
        'pyobjc',
        'pytest',
        'PyTweening',
        'webcolors',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Quality Assurance',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)
