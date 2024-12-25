astropy-samp-ds9
================

Launch and interact with [SAOImageDS9](https://github.com/SAOImageDS9/SAOImageDS9) using the [SAMP protocol](http://www.ivoa.net/Documents/latest/SAMP.html), and client libraries provided by [Astropy SAMP](https://docs.astropy.org/en/stable/samp/index.html).

- requires SAOImageDS9 >= 8.7 (yet to be released on official channels, but available from github).

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

More advanced features include: exit handler, use pre-existing SAMP hub, etc.
As of now, this project has no documention. Read the code!

