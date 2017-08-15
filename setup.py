from os import path

from setuptools import find_packages, setup


here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name="pgantomizer",
    version='0.1.1',
    description="Anonymize data in your PostgreSQL dababase with ease.",
    long_description=long_description,
    author='Oskar Hollmann',
    author_email='oskar@hollmann.me',
    url='https://github.com/asgeirrr/pgantomizer',
    license='BSD',
    package_dir={'pgantomizer': 'pgantomizer'},
    include_package_data=True,
    packages=find_packages(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6',
        'Topic :: Database :: Front-Ends',
    ],
    keywords='postgres anonymization dump',
    install_requires=[
        'psycopg2>=2.6.1',
        'pyyaml>=3.11',
    ],
    setup_requires=[
        'pytest-runner',
    ],
    tests_require=[
        'pytest',
        'pytest-postgresql==1.3.0',
    ],
    entry_points={
        'console_scripts': [
            'pgantomizer_dump=pgantomizer.dump:main',
            'pgantomizer=pgantomizer.anonymize:main'
        ]
    }
)
