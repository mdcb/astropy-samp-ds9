#!/usr/bin/env python3

from astropy.samp import SAMPIntegratedClient
from astropy.samp.errors import SAMPHubError, SAMPProxyError
from pathlib import Path
import subprocess
import sys
import os
import re
import shlex
import time

#import threading
#import atexit
#import signal

# environment
SAMP_HUB_EXE = os.environ.get('SAMP_HUB_EXE', 'samp_hub') # samp_hub exectuable provided by astropy
SAMP_HUB_PATH = os.environ.get('SAMP_HUB_PATH', f"{os.environ['HOME']}/.samp-ds9") # path to samp files

class DS9Hub:

    def __init__(self,
                 name,
                 timeout=15,                                    # time for hub to be fully SAMP functional (seconds)
                 init_retry_time=1,                             # time to sleep between retries on init (seconds)
                 debug=False
                 ):
        '''
        Start a hub with a given name.
        The name is attached to: name, display, userid.
        If it already exists and is alive, it's a noop.
        daemonize: make it persistent (let the hub running after python exits).
        '''
        user = os.environ.get('USER', 'anonymous')
        display = os.environ.get('DISPLAY', 'headless')
        # generate a SAMP_HUB from name, user and display
        Path(SAMP_HUB_PATH).mkdir(mode=0o700, parents=True, exist_ok=True)
        samp_hub_name = f"hub_{name}_{user}_{display}"
        samp_hub_name = re.sub(r'[^A-Za-z0-9\.:]', '_', samp_hub_name) # sanitized
        self.samp_hub_file = f"{SAMP_HUB_PATH}/{samp_hub_name}.samp"
        # check if the hub is already up
        os.environ['SAMP_HUB'] = f"std-lockurl:file://{self.samp_hub_file}"
        if not self._connect_hub(debug=debug):
            # spawn a new one
            cmd = f"{SAMP_HUB_EXE} --no-web-profile --label \"{samp_hub_name}\"" #  --lockfile {self.samp_hub_file}
            if debug: cmd += f" --log-output {SAMP_HUB_PATH}/{samp_hub_name}.log --log-level DEBUG"
            else: cmd += ' --log-level ERROR'
            __process = subprocess.Popen(shlex.split(cmd), start_new_session=True, env=os.environ)
            if not self._connect_hub(timeout=timeout, init_retry_time=init_retry_time, debug=debug):
                try: __process.terminate()
                except: pass
                raise RuntimeError(f"failed to launch hub {name}")

    def _connect_hub(self, timeout=0, init_retry_time=1, debug=False):
        if debug: print('looking for SAMP hub ...')
        __hub_found = False
        __samp = SAMPIntegratedClient(callable=False)
        # XXX suppress show_progress output from astropy/utils/data.py, overriding isatty
        __tty = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
        if __tty:
            __tty= getattr(sys.stdout, 'isatty')
            sys.stdout.isatty = lambda: False
        tstart = time.time()
        while True:
            try:
                __samp.connect()
                # __samp.disconnect()
                __hub_found = True
                break
            except (SAMPHubError, SAMPProxyError) as e:
                if debug: print(f'_connect_hub exception: {e!r}')
                if time.time() - tstart > timeout: break
                time.sleep(init_retry_time)
        # undo isatty hack
        if __tty: sys.stdout.isatty = __tty
        if debug: print(f"SAMP hub found: {__hub_found}")
        return __hub_found

