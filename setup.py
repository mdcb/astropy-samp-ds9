from setuptools import setup

setup(
    name='ds9SAMP',
    version='0.1.0',    
    description='Interact with SAOImageDS9 using Astropy SAMP',
    long_description='Interact with SAOImageDS9 using Astropy SAMP',
    long_description_content_type='text/x-rst',
    url='https://github.com/mdcb908/ds9SAMP',
    author='Matthieu Bec',
    author_email='mdcb808@gmail.com',
    license='GPL-3.0',
    packages=['ds9SAMP'],
    install_requires=['astropy'],
    classifiers=[
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',  
        'Operating System :: POSIX :: Linux',        
        #'Programming Language :: Python :: 2',
        #'Programming Language :: Python :: 2.7',
        #'Programming Language :: Python :: 3',
        #'Programming Language :: Python :: 3.4',
        #'Programming Language :: Python :: 3.5',
    ],
)
