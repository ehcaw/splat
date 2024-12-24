
import threading
import time

class ProcessMonitor:
    def __init__(self, term_sesh):
        self.term_sesh = term_sesh
        self.monitor_thread = None
        self.is_running = False

    def start_monitoring(self):
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self.monitor_tmux)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        print('monitor thread starting')
    def monitor_tmux(self):
        while self.is_running:
            output = self.term_sesh.read_tmux_output()
            if output:
                self.term_sesh.publisher.send_json({
                    'type': 'tmux_output',
                    'data': output,
                    'timestamp': time.time()
                })
            time.sleep(1)
