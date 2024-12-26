astropy-samp-ds9
================

Launch and interact with [SAOImageDS9](https://github.com/SAOImageDS9/SAOImageDS9), using the [SAMP](http://www.ivoa.net/Documents/latest/SAMP.html) protocol and client libraries provided by [Astropy SAMP](https://docs.astropy.org/en/stable/samp/index.html).

Example
-------

```
from astropy_samp_ds9.launcher import DS9

ds9 = DS9(title='hello world')
res = ds9.get('version')
ds9.set('cmap cool', 'scale zscale', 'zoom to fit')
ds9.set('mosaicimage wcs {my.fits}')
res = ds9.get('iexam key coordinate')
```

Environment
-----------

* DS9_EXE

This package requires SAOImageDS9 >= 8.7 (as of 2024-12-26, yet to be released on official channels, but available from github).
By default, it uses `ds9` that satisfies this release and is in your PATH.

If you have several ds9 installations on your machine, or ds9 is not in your path, use
the DS9_EXE environment to specify the ds9 executable location.
For example: `export DS9_EXE=/usr/local/ds9/8.7/bin/ds9`

* SAMP_HUB_PATH

The directoty being used for SAMP_HUB files.
By default, it will use `$HOME/.samp-ds9/`, and create this directory as needed.


Miscellaneous
-------------

More advanced features include: exit handler, use pre-existing SAMP hub, etc.
As of now, this project has no documention. Read the code!

