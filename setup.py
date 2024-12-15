from setuptools import setup

setup(
    name='ds9SAMP',
    version='0.1.1',
    description='Interact with SAOImageDS9 using Astropy SAMP',
    long_description='Interact with SAOImageDS9 using Astropy SAMP',
    long_description_content_type='text/x-rst',
    url='https://github.com/mdcb/ds9SAMP',
    author='Matthieu Bec',
    author_email='mdcb808@gmail.com',
    license='GPL-3.0',
    packages=['ds9SAMP'],
    install_requires=['astropy'], # XXX 5.3.3 ?
    classifiers=[
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3', # XXX 3.12 ?
    ],
)
