from distutils.core import setup

setup(
    name='macUITest',
    packages=['macUITest'],
    version='0.1',
    license='Apache-2.0 License',
    description='A simple UI testing framework for macOS',
    author='Andrii Kislitsyn',
    author_email='andriikislitsyn@gmail.com',
    url='https://github.com/andriykislitsyn',
    download_url='https://github.com/andriykislitsyn/macuitest/archive/v0.1-alpha.tar.gz',
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
        'Intended Audience :: Automation',
        'Topic :: Software Development :: Quality Assurance Automation', 'License :: Apache-2.0 License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)
