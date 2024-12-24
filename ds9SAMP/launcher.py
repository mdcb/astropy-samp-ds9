#!/usr/bin/env python3

from astropy.samp import SAMPIntegratedClient
from astropy.samp.errors import SAMPHubError
from datetime import datetime, UTC
from pathlib import Path
import subprocess
import threading
import atexit
import signal
import shlex
import time
import os
import re

# environment
DS9_EXE = os.environ.get('DS9_EXE', 'ds9v8.7') # requires ds9 >= v8.7
SAMP_HUB_PATH = os.environ.get('SAMP_HUB_PATH', f"{os.environ['HOME']}/.samp-ds9") # path to samp files

# XXX Do not use spaces in title until this issue is resolved https://github.com/SAOImageDS9/SAOImageDS9/issues/206
# XXX To fix it yourself:
# XXX diff --git a/ds9/library/samp.tcl b/ds9/library/samp.tcl
# XXX index 004642c4f..7e984d791 100644
# XXX --- a/ds9/library/samp.tcl
# XXX +++ b/ds9/library/samp.tcl
# XXX @@ -17,7 +17,7 @@ proc SAMPConnectMetadata {} {
# XXX      global samp
# XXX      global ds9
# XXX
# XXX -    set map(samp.name) "string $ds9(title)"
# XXX +    set map(samp.name) "string \"$ds9(title)\""


class DS9:

    def __init__(self,
                 title='ds9SAMP',                               # ds9 window title, and SAMP name
                 timeout=15,                                    # time for ds9 to be fully SAMP functional (seconds)
                 exit_callback=None,                            # callback function to invoke when ds9 dies
                 kill_on_exit=False,                            # kill main process on exit
                 ds9args='-geometry 1024x768 -colorbar no',     # ds9 window title, and SAMP name
                 # rarely used options                          #
                 poll_alive_time=5,                             # is_alive poll thread period time (seconds)
                 init_retry_time=1,                             # time to sleep between retries on init (seconds)
                 debug=False,                                   # debug output
                 samp_hub_file=None                             # use provided samp_hub_file rather than start a hub from ds9
                ):
        self.debug = debug
        self.exit_callback = exit_callback
        self.kill_on_exit = kill_on_exit
        self.__lock = threading.Lock()      # Threaded SAMP access
        self.__evtexit = threading.Event()  # event to exit
        self.__pid = os.getpid()            # process PID
        # exit handler
        atexit.register(self.exit, use_callback=False, main_thread=True)
        try:
            if samp_hub_file:
                samp_hub_cmd = '-samp hub no'
                self.__samp_hub_file = None
            else:
                samp_hub_cmd = '-samp hub yes'
                # generate a unique SAMP_HUB from title, timestamp, process PID
                Path(SAMP_HUB_PATH).mkdir(mode=0o700, parents=True, exist_ok=True)
                tnow = datetime.now(UTC)
                samp_hub_name = f"{title}_utc{tnow.strftime('%Y%m%dT%H%M%S')}.{tnow.microsecond:06d}_pid{self.__pid}"
                samp_hub_name = re.sub(r'[^A-Za-z0-9\\.]', '_', samp_hub_name) # sanitized
                self.__samp_hub_file = f"{SAMP_HUB_PATH}/{samp_hub_name}.samp"
            cmd = f"{DS9_EXE} -samp client yes {samp_hub_cmd} -samp web hub no -xpa no -unix none -fifo none -port 0 -title '{title}' {ds9args}"
            os.environ['SAMP_HUB'] = f"std-lockurl:file://{self.__samp_hub_file}"
            os.environ['XMODIFIERS'] = '@im=none' # fix ds9 (Tk) responsiveness on Wayland. see https://github.com/ibus/ibus/issues/2324#issuecomment-996449177
            if self.debug:print(f"SAMP_HUB: {os.environ['SAMP_HUB']}")
            # XXX TODO signal handler
            # spawn ds9
            if self.debug: print('spawning ds9')
            self.__process = subprocess.Popen(shlex.split(cmd), start_new_session=True, env=os.environ)
            # SAMP
            self.__samp = SAMPIntegratedClient(name=f"{title} controller", callable=False)
            self.__samp_clientId = None
            tstart = time.time()
            # wait for SAMP hub
            while True:
                if self.debug: print('looking for SAMP hub ...')
                try:
                    self.__samp.connect() # XXX supress output: Downloading ...  test: sys.stdout.isatty(), show_progress is not accessible from astropy/utils/data.py
                    if self.debug: print('found SAMP hub')
                    break
                except SAMPHubError:
                    if time.time() - tstart > timeout: raise RuntimeError(f"hub not found (timeout: {timeout})")
                    time.sleep(init_retry_time)
            # wait for ds9
            while True:
                if self.debug: print('looking for ds9')
                self.__samp_clientId = self.__get_samp_clientId(title)
                if self.__samp_clientId:
                    if self.debug: print('found ds9')
                    break
                if time.time() - tstart > timeout: raise RuntimeError(f"ds9 not found (timeout: {timeout})")
                time.sleep(init_retry_time)
            # poll_alive
            if poll_alive_time > 0:
                self.__watcher = threading.Thread(target=self.__watch_thread, args=(poll_alive_time,)) # our thread keeps a reference to self, making self undertructible until the thread stops
                self.__watcher.daemon = True
                self.__watcher.start()
        except Exception as e:
            self.exit()
            raise e

    def __del__(self):
        if self.debug: print('destructor')
        self.exit(use_callback=False, main_thread=True)

    def exit(self, use_callback=True, main_thread=True):
        if self.debug: print('__evtexit')
        try: self.__evtexit.set()
        except: pass
        if main_thread:
            if self.debug: print('join')
            try: self.__watcher.join(timeout=1)
            except: pass
        if self.debug: print('exit')
        try: self.set('exit')
        except: pass
        if self.debug: print('kill')
        try: self.__process.kill() # XXX terminate() ?
        except: pass
        if self.__samp_hub_file:
            if self.debug: print('rm hubfile')
            try: Path(self.__samp_hub_file).unlink(missing_ok=True)
            except: pass
        if self.exit_callback:
            if self.debug: print('exit_callback')
            try: self.exit_callback()
            except: pass
        if self.kill_on_exit:
            if self.debug: print('kill_on_exit')
            try: os.kill(self.__pid, signal.SIGTERM)
            except: pass

    def __get_samp_clientId(self, title):
        for c_id in self.__samp.get_subscribed_clients('ds9.set'): # note: it's a dict
            c_meta = self.__samp.get_metadata(c_id)
            if self.debug: print(f"...clientId {c_id} = {c_meta['samp.name']}")
            if c_meta['samp.name'] == title:
                return c_id
        return None

    def alive(self):
        try:
            with self.__lock:
                msg = self.__samp.enotify(self.__samp_clientId, 'samp.app.ping')
                if self.debug: print(f"ping replied >{msg}<")
                # ds9 = 'OK', astropy.samp.hub = {} ... assume any reply is ok
                return True
        except: return False

    def __watch_thread(self, period):
        if self.debug: print(f"watch_thread started - period {period}")
        while True:
            if self.debug: print('...watching')
            if self.__evtexit.wait(timeout=period):
                if self.debug: print('watch_thread quits gracefully')
                break
            if not self.alive():
                if self.debug: print('watch_thread ds9 is not alive')
                break
        self.exit(main_thread=False)
        if self.debug: print('watch_thread exit')

    def set(self, *cmds, timeout=10):
        with self.__lock:
            for cmd in cmds:
                self.__samp.ecall_and_wait(self.__samp_clientId, 'ds9.set', f"{int(timeout)}", cmd=cmd)

    def get(self, cmd, timeout=10):
        with self.__lock:
            # {'samp.result': {'value': '...'}, 'samp.status': 'samp.ok'}
            rc = self.__samp.ecall_and_wait(self.__samp_clientId, 'ds9.get', f"{int(timeout)}", cmd=cmd)
            if self.debug: print(f"get {cmd} return: {rc}")
            if rc['samp.status'] == 'samp.ok':
                return rc['samp.result'].get('value')
            else:
                raise RuntimeError(f"get {cmd} returned: {rc}")

if __name__ == '__main__':
    ds9 = DS9('hello world')
    res = ds9.get('version')
    print(res) # 'hello world 8.7b1'
