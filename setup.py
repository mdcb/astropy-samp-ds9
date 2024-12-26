from setuptools import setup

import sys
sys.path.insert(0,'')
from astropy_samp_ds9.__init__ import __version__

setup(
    name='astropy-samp-ds9',
    version=__version__,
    description='Launch and interact with SAOImageDS9 using Astropy SAMP',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/mdcb/astropy-samp-ds9',
    author='Matthieu Bec',
    author_email='mdcb808@gmail.com',
    license='GPL-3.0',
    packages=['astropy_samp_ds9'],
    install_requires=['astropy'], # XXX 5.3.3 ?
    classifiers=[
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3', # XXX 3.12 ?
    ],
)
