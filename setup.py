#!/usr/bin/env python
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

def requireModules(moduleNames=None):
    import re
    if moduleNames is None:
        moduleNames = []
    else:
        moduleNames = moduleNames

    commentPattern = re.compile(r'^\w*?#')
    moduleNames.extend(
        filter(lambda line: not commentPattern.match(line),
            open('requirements.txt').readlines()))

    return moduleNames

setup(
    name='RunLoad',
    version='0.2.5.2',

    author='Ilya Krylov',
    author_email='ilya.krylov@gmail.com',

    description='RunLoad - Yandex.Tank HTTP API Client for CLI',
    long_description=open('README.txt').read(),
    classifiers=[
        'Development Status :: Alpha',
        'Intended Audience :: Developers'
    ],

    install_requires=requireModules(),
    packages=['tank_api_client'],
    package_dir={'tank_api_client': 'tank_api_client'},
    package_data={
        'tank_api_client': [],
    },
    scripts=['scripts/runload', 'scripts/peakscount'],
    test_suite='runload',
)
