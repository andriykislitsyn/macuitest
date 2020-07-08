import signal
import threading
import time

from ApplicationServices import AXObserverGetRunLoopSource, NSDefaultRunLoopMode
from CoreFoundation import CFRunLoopAddSource, CFRunLoopGetCurrent
from PyObjCTools import AppHelper
from PyObjCTools import MachSignals

from lib.elements.ax11.callbacks import (PAXObserverAddNotification, PAXObserverCallback, PAXObserverCreate,
                                         PAXObserverRemoveNotification, )


def stop_event_loop():
    AppHelper.stopEventLoop()
    raise KeyboardInterrupt("Keyboard interrupted Run Loop")


class Observer:
    def __init__(self, ui_element=None):
        self.ref = ui_element
        self.callback = None
        self.callback_result = None

    def wait_for(self, notification=None, filter_=None, timeout=5):
        self.callback_result = None

        @PAXObserverCallback
        def _callback(element):
            ret_element = self.ref.__class__(element)
            if filter_(ret_element):
                self.callback_result = ret_element

        observer = PAXObserverCreate(self.ref.pid, _callback)

        PAXObserverAddNotification(observer, self.ref.ref, notification, id(self.ref.ref))

        # Add observer source to run loop
        CFRunLoopAddSource(CFRunLoopGetCurrent(), AXObserverGetRunLoopSource(observer), NSDefaultRunLoopMode, )

        def event_stopper():
            end_time = time.time() + timeout
            while time.time() < end_time:
                if self.callback_result is not None:
                    break
            AppHelper.callAfter(AppHelper.stopEventLoop)

        event_watcher = threading.Thread(target=event_stopper)
        event_watcher.daemon = True
        event_watcher.start()

        # Set the signal handlers prior to running the run loop
        old_sig_int_handler = MachSignals.signal(signal.SIGINT, stop_event_loop)
        AppHelper.runConsoleEventLoop()
        MachSignals.signal(signal.SIGINT, old_sig_int_handler)
        PAXObserverRemoveNotification(observer, self.ref.ref, notification)
        return self.callback_result
