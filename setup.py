# ! important
# see https://stackoverflow.com/a/27868004/1497139
from setuptools import setup
from collections import OrderedDict

# read the contents of your README file
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='pyOpenSourceProjects',
    version='0.0.8',

    packages=['osprojects',],
    author='Wolfgang Fahl',
    author_email='wf@bitplan.com',
    maintainer='Wolfgang Fahl',
    url='https://github.com/WolfgangFahl/pyOpenSourceProjects',
    project_urls=OrderedDict(
        (
            ("Documentation", "http://wiki.bitplan.com/index.php/pyOpenSourceProjects"),
            ("Code", "https://github.com/WolfgangFahl/pyOpenSourceProjects"),
            ("Issue tracker", "https://github.com/WolfgangFahl/pyOpenSourceProjects/issues"),
        )
    ),
    license='Apache License',
    description='',
    install_requires=[
          'pyLodStorage~=0.2.0',
          'py-3rdparty-mediawiki~=0.6.1',
    ],
    classifiers=[
            'Programming Language :: Python',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9'
    ],
    long_description=long_description,
    long_description_content_type='text/markdown',
    entry_points={
        'console_scripts': [
            'issue2ticket = osprojects.osproject:main',
            'gitlog2wiki = osprojects.osproject:gitlog2wiki',
        ]
    }
)
