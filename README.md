astropy-samp-ds9
================

Launch and interact with [SAOImageDS9](https://github.com/SAOImageDS9/SAOImageDS9), using the [SAMP](http://www.ivoa.net/Documents/latest/SAMP.html) protocol and client libraries provided by [Astropy SAMP](https://docs.astropy.org/en/stable/samp/index.html).

Installation
------------

Using PyPI [astropy-samp-ds9](https://pypi.org/project/astropy-samp-ds9/).

```
pip install astropy-samp-ds9
```

Example
-------

* single ds9 instance (managing its own hub)

```
from astropy_samp_ds9.launcher import DS9

ds9 = DS9(title='hello world')
res = ds9.get('version')
ds9.set('cmap cool', 'scale zscale', 'zoom to fit')
ds9.set('mosaicimage wcs {my.fits}')
res = ds9.get('iexam key coordinate')
```

* ds9 instance(s) attached to an external hub. Those can be attached, re-attached, and controlled from different sessions.

```
from astropy_samp_ds9.hublauncher import DS9Hub
from astropy_samp_ds9.launcher import DS9

hub = DS9Hub(name='myhub')
samp_hub_file = hub.samp_hub_file

ds9red = DS9(title='red channel', kill_ds9_on_exit=False, samp_hub_file=samp_hub_file)
ds9blue = DS9(title='blue channel', kill_ds9_on_exit=False, samp_hub_file=samp_hub_file)

```

Environment
-----------

* DS9_EXE

This package requires SAOImageDS9 >= 8.7b1.
By default, it uses `ds9` that must satisfy this version and found in your PATH.

If you have several ds9 installations on your machine, or ds9 is not in your path, use
the DS9_EXE environment to specify the ds9 executable location.
For example: `export DS9_EXE=/usr/local/ds9/8.7/bin/ds9`

* SAMP_HUB_PATH

The directory used to store SAMP_HUB files.
By default, it will use `$HOME/.samp-ds9/`, and create this directory as needed.

* SAMP_HUB_EXE

The samp_hub executable provided by astropy.
By default, it will use `samp_hub` that must be in your PATH.

Miscellaneous
-------------

More advanced features include: exit handler, use pre-existing SAMP hub, etc.
As of now, the documention is lacking and still WIP. Read the code!

