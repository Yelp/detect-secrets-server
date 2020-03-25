from setuptools import find_packages
from setuptools import setup

import detect_secrets_server


setup(
    name='detect_secrets_server',
    packages=find_packages(exclude=(['test*', 'tmp*'])),
    version=detect_secrets_server.__version__,
    description='Tool for setting up a detect-secrets server',
    long_description=(
        'Check out detect-secrets-server on '
        '`GitHub <https://github.com/Yelp/detect-secrets-server>`_!'
    ),
    license="Copyright Yelp, Inc. 2018",
    author='Aaron Loo',
    author_email='aaronloo@yelp.com',
    url='https://github.com/Yelp/detect-secrets-server',
    download_url='https://github.com/Yelp/detect-secrets-server/archive/{}.tar.gz'.format(detect_secrets_server.__version__),
    keywords=[
        'secret-management',
        'pre-commit',
        'security',
        'entropy-checks'
    ],
    install_requires=[
        'detect-secrets>=0.13.0',
        'pyyaml',
        'unidiff',
    ],
    extras_require={
        'cron': [
            'python-crontab',
        ],
    },
    entry_points={
        'console_scripts': [
            'detect-secrets-server = detect_secrets_server.__main__:main',
        ],
    },
    classifiers=[
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
