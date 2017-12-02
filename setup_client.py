import os
from setuptools import find_packages, setup

VERSION = os.environ.get('VERSION', '0.121.X')
RELEASE = os.environ.get('RELEASE', '.dev')

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
#os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

with open('worker_requirements.txt', 'r') as f:
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
    name='workflow_client',
    version='%s%s' % (VERSION, RELEASE),
    packages=prepend_find_packages('workflow_client'),
    include_package_data=True,
    license='Allen Institute Software License',
    description='Blue Sky Workflow Client',
    long_description=README,
    url='https://github.com/AllenInstitute',
    author='Tim Fliss',
    author_email='timf@alleninstitute.org',
    install_requires = required,
    tests_require=test_required,
    setup_requires=[
        'flake8'
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Celery',
        'Framework :: Celery :: 4.0.2',
        'Intended Audience :: Developers',
        'License :: Allen Institute Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
