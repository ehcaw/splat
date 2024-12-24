import threading
import time
import readline
from zap import TermSesh
class ProcessMonitor:
    def __init__(self, term_sesh: TermSesh):
        self.term_sesh = term_sesh
        self.stdout_thread = None
        self.stderr_thread = None
        self.is_running = False

    def start_monitoring(self):
        """Start monitoring stdout and stderr in separate threads"""
        if not self.term_sesh or not self.term_sesh.terminal_process:
            print("No terminal process to monitor")
            return False

        if not self.term_sesh.terminal_stdout or not self.term_sesh.terminal_stderr:
            print("No stdout/stderr streams available")
            return False

        self.is_running = True
        self.stdout_thread = threading.Thread(target=self._monitor_stdout)
        self.stderr_thread = threading.Thread(target=self._monitor_stderr)

        self.stdout_thread.daemon = True
        self.stderr_thread.daemon = True

        self.stdout_thread.start()
        self.stderr_thread.start()
        return True

    def _monitor_stdout(self):
        """Monitor stdout and send updates through ZMQ"""
        if not self.term_sesh.terminal_stdout:
            return

        for line in iter(self.term_sesh.terminal_stdout.readline, ''):
            if not self.is_running:
                break
            if line:
                try:
                    self.term_sesh.publisher.send_json({
                        'type': 'stdout',
                        'data': line.strip(),
                        'pid': self.term_sesh.terminal_process.pid if self.term_sesh.terminal_process else 0,
                        'timestamp': time.time()
                    })
                except Exception as e:
                    print(f"Error sending stdout: {e}")

    def _monitor_stderr(self):
        """Monitor stderr and send updates through ZMQ"""
        if not self.term_sesh.terminal_stderr:
            return

        for line in iter(self.term_sesh.terminal_stderr.readline, ''):
            if not self.is_running:
                break
            if line:
                try:
                    self.term_sesh.publisher.send_json({
                        'type': 'stderr',
                        'data': line.strip(),
                        'pid': self.term_sesh.terminal_process.pid if self.term_sesh.terminal_process else 0,
                        'timestamp': time.time()
                    })
                except Exception as e:
                    print(f"Error sending stderr: {e}")
