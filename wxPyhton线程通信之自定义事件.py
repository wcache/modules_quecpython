import threading
import time
from threading import *
import wx

# Define notification event for thread completion
EVT_RESULT_ID = wx.NewId()


def EVT_RESULT(win, func):
    """Define Result Event."""
    win.Connect(-1, -1, EVT_RESULT_ID, func)


class ResultEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_RESULT_ID)
        self.data = data


# Thread class that executes processing
class WorkerThread(Thread):
    """Worker Thread Class."""

    def __init__(self, notify_window):
        """Init Worker Thread Class."""
        Thread.__init__(self)
        self.setDaemon(True)
        self._notify_window = notify_window
        self._want_abort = threading.Event()
        # This starts the thread running on creation, but you could
        # also make the GUI thread responsible for calling this

    def run(self):
        """Run Worker Thread."""
        # This is the code executing in the new thread. Simulation of
        for i in range(10):
            time.sleep(1)
            if self._want_abort.isSet():
                # Use a result of None to acknowledge the abort (of
                # course you can use whatever you'd like or even
                # a separate event type)
                wx.PostEvent(self._notify_window, ResultEvent(None))
                return
            wx.PostEvent(self._notify_window, ResultEvent(i))
        # Here's where the result would be returned (this is an
        # example fixed result of the number 10, but it could be
        # any Python object)
        wx.PostEvent(self._notify_window, ResultEvent(10))

    def abort(self):
        """abort worker thread."""
        # Method for use by main thread to signal an abort
        print('222')
        self._want_abort.set()


# GUI Frame class that spins off the worker thread
class MainFrame(wx.Frame):
    """Class MainFrame."""

    def __init__(self, parent, id):
        """Create the MainFrame."""
        wx.Frame.__init__(self, parent, id, 'Thread Test')

        # Dumb sample frame with two buttons
        self.OkButton = wx.Button(self, wx.ID_ANY, 'Start', pos=(0, 0))
        self.StopButton = wx.Button(self, wx.ID_ANY, 'Stop', pos=(0, 50))
        self.status = wx.StaticText(self, -1, '', pos=(0, 100))

        self.Bind(wx.EVT_BUTTON, self.OnStart, self.OkButton)
        self.Bind(wx.EVT_BUTTON, self.OnStop, self.StopButton)

        # Set up event handler for any worker thread results
        EVT_RESULT(self, self.OnResult)

        # And indicate we don't have a worker thread yet
        self.worker = None

    def __Onfunc(self):
        import time
        time.sleep(10)

    def OnStart(self, event):
        """Start Computation."""
        # Trigger the worker thread unless it's already busy
        print('self on start: ', self)
        if not self.worker:
            self.status.SetLabel('Starting computation')
            self.worker = WorkerThread(self)
            self.worker.start()
            print('work on start: ', self.worker)

    def OnStop(self, event):
        """Stop Computation."""
        # Flag the worker thread to stop if running
        print('self on stop: ', self)
        print('work on stop: ', self.worker)
        if self.worker is not None:
            self.status.SetLabel('Trying to abort computation')
            self.worker.abort()
            self.worker = None

    def OnResult(self, event):
        """Show Result status."""

        # Process results here
        self.status.SetLabel('Computation Result: %s' % event.data)
        # In either event, the worker is done
        # self.worker = None


class MainApp(wx.App):
    """Class Main App."""

    def OnInit(self):
        """Init Main App."""
        self.frame = MainFrame(None, -1)
        self.frame.Show(True)
        self.SetTopWindow(self.frame)
        return True


if __name__ == '__main__':
    app = MainApp(0)
    app.MainLoop()
