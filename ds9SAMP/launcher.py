#!/usr/bin/env python3

from astropy.samp.errors import SAMPHubError
from astropy.samp import SAMPIntegratedClient
from datetime import datetime, UTC
from pathlib import Path
import atexit
import os
import re
import shlex
import signal
import subprocess
import threading
import time

###

DS9_EXE = '/home/mdcb/work/webrepos/SAOImageDS9/bin/ds9'
SAMP_HUB_PATH = f"{os.environ['HOME']}/.samp-lbto"

###

class DS9:

    def __init__(self,
                 title='lbto ds9',      # ds9 window title, and SAMP name
                 timeout=15,            # time for ds9 to be fully SAMP functional (seconds)
                 exit_callback=None,    # callback function to invoke when ds9 dies
                 kill_on_exit=False,    # kill main process on exit
                 # rarely used options  #
                 poll_alive_time=5,    # is_alive poll thread period time (seconds)
                 init_retry_time=1,     # time to sleep between retries on init (seconds)
                 debug=False            # debug output
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
            # unique SAMP_HUB from title, timestamp, process PID
            Path(SAMP_HUB_PATH).mkdir(mode=0o700, parents=True, exist_ok=True)
            tnow = datetime.now(UTC)
            samp_hub_name = f"{title}_utc{tnow.strftime('%Y%m%dT%H%M%S')}.{tnow.microsecond:06d}_pid{self.__pid}"
            samp_hub_name = re.sub(r'[^A-Za-z0-9\\.]', '_', samp_hub_name) # sanitized
            self.__samp_hub_file = f"{SAMP_HUB_PATH}/{samp_hub_name}.samp"
            os.environ['SAMP_HUB'] = f"std-lockurl:file://{self.__samp_hub_file}"
            os.environ['XMODIFIERS'] = '@im=none' # https://github.com/ibus/ibus/issues/2324#issuecomment-996449177
            if self.debug:
                print(f"SAMP_HUB {os.environ['SAMP_HUB']}")
                print(f"file {self.__samp_hub_file}")
            # signal handler
            pass # XXX TODO
            # spawn ds9
            # XXX -samp arguments so it does not rely on ~/ds9/*.pref
            if self.debug: print('spawning ds9')
            cmd = f"{DS9_EXE} -title '{title}' -geometry 1024x768 -colorbar no"
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
                self.__watcher = threading.Thread(target=self.watch_thread, args=(poll_alive_time,)) # our thread keeps a reference to self, making self undertructible until the thread stops
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

    def __isalive(self):
        try:
            with self.__lock:
                return self.__samp.enotify(self.__samp_clientId, 'samp.app.ping') == 'OK' # 'OK' response implemented by ds9, not an internal SAMP protocol
        except: return False

    def watch_thread(self, period):
        if self.debug: print(f"watch_thread started - period {period}")
        while True:
            if self.debug: print('...watching')
            if self.__evtexit.wait(timeout=period):
                if self.debug: print('watch_thread quits gracefully')
                break
            if not self.__isalive():
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
            return self.__samp.ecall_and_wait(self.__samp_clientId, 'ds9.get', f"{int(timeout)}", cmd=cmd)

if __name__ == '__main__':
    ds9 = DS9('hello world', 250)
    print('found ds9!')
    res = ds9.get('version')
    print(res)
    # {'samp.result': {'value': 'hello world 8.7b1'}, 'samp.status': 'samp.ok'}
