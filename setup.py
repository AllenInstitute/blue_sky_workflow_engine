import os
from setuptools import find_packages, setup

VERSION = '0.121.0'


with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

with open('requirements.txt', 'r') as f:
    required = f.read().splitlines()

with open('test_requirements.txt', 'r') as f:
    test_required = f.read().splitlines()

def prepend_find_packages(*roots):
    ''' Recursively traverse nested packages under the root directories
    '''
    packages = []

    for root in roots:
        packages += [root]
        packages += [root + '.' + s for s in find_packages(root)]
        
    return packages

setup(
    name='django-blue-sky-workflow-engine',
    version='%s' % (VERSION),
    scripts=[
        os.path.join('bin', 'restart_workers.sh'),
        os.path.join('bin', 'setup_blue_green.sh')
    ],
    packages=prepend_find_packages('workflow_engine', 'workflow_client'),
    package_data={'': ['*.conf', '*.cfg', '*.json', '*.env', '*.sh', '*.txt', '*.pbs', 'Makefile'] },
    include_package_data=True,
    license='Allen Institute Software License',
    description='Blue Sky Workflow Engine',
    long_description=README,
    url='https://github.com/AllenInstitute',
    author='Nathan Sjoquist',
    author_email='nathans@alleninstitute.org',
    install_requires=required,
    tests_require=test_required,
    setup_requires=[
        'flake8'
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 2.2',
        'Intended Audience :: Developers',
        'License :: Allen Institute Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Topic :: Internet :: WWW/HTTP'
    ]
)
