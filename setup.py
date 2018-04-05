from setuptools import find_packages
from setuptools import setup


VERSION = '0.1.0'

setup(
    name='detect_secrets_server',
    packages=find_packages(exclude=(['test*', 'tmp*'])),
    version=VERSION,
    description='Tool for setting up a detect-secrets server',
    long_description="Check out detect-secrets-server on `GitHub <https://github.com/Yelp/detect-secrets-server>`_!",
    license="Copyright Yelp, Inc. 2018",
    author='Aaron Loo',
    author_email='aaronloo@yelp.com',
    url='https://github.com/Yelp/detect-secrets-server',
    download_url='https://github.com/Yelp/detect-secrets-server/archive/{}.tar.gz'.format(VERSION),
    keywords=['secret-management', 'pre-commit', 'security', 'entropy-checks'],
    install_requires=[
        'boto3',
        'detect-secrets',
        'enum34',
        'future',
        'pysensu_yelp',
        'pyyaml',
        'unidiff',
    ],
    entry_points={
        'console_scripts': [
            'detect-secrets-server = detect_secrets_server.__main__:main',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Intended Audience :: Developers",
        "Topic :: Software Development",
        "Topic :: Utilities",
        "Environment :: Console",
        "Operating System :: OS Independent",
        "Development Status :: 5 - Production/Stable",
    ]
)
