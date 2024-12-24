# auto_debugger.py
import os
import platform
import subprocess
import time
import zmq
import base64
import zlib
from typing import Optional, List
import threading
import re
import traceback
import select
#from relational import relational_error_parsing_function

def open_new_terminal(command: str) -> subprocess.Popen:
    if platform.system() == "Windows":
        # Windows command to open new terminal
        return subprocess.Popen(
            ['start', 'cmd', '/k'] + command.split(),
            shell=True
        )
    elif platform.system() == "Darwin":  # macOS
        apple_script = (
            f'tell application "Terminal" to do script "cd {os.getcwd()} && '
            f'{command}"'
        )
        return subprocess.Popen(['osascript', '-e', apple_script])
    else:  # Linux
        # Detect the available terminal emulator
        terminals = ['gnome-terminal', 'xterm', 'konsole']
        terminal_cmd = None

        for term in terminals:
            if subprocess.run(['which', term],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE).returncode == 0:
                terminal_cmd = term
                break

        if terminal_cmd:
            if terminal_cmd == 'gnome-terminal':
                return subprocess.Popen([
                    terminal_cmd, '--', 'bash', '-c',
                    f'cd {os.getcwd()} && {command}; exec bash'
                ])
            else:
                return subprocess.Popen([
                    terminal_cmd, '-e',
                    f'bash -c "cd {os.getcwd()} && python {command}; exec bash"'
                ])
        else:
            raise EnvironmentError("No supported terminal emulator found")

class TermSesh:
    def __init__(self, port=5555, terminal_app=None):
        self.context = zmq.Context()
        self.publisher = self.context.socket(zmq.PUB)
        self.publisher.bind(f"tcp://*:{port}")
        self.system = platform.system()
        self.terminal_app = terminal_app
        self.terminal_process = None
        self.terminal_stdout = None
        self.terminal_stderr = None
        self.terminal_stdin = None
        self.monitor = None


    def send_code_segment(self, code_data):
        """
        Send code segments with metadata
        code_data = {
            'file_path': 'path/to/file',
            'code': 'actual code content',
            'metadata': {...},
            'action': 'analyze/edit/debug'
        }
        """
        # Compress the code content
        compressed_code = base64.b64encode(
            zlib.compress(code_data['code'].encode())
        ).decode()
        code_data['code'] = compressed_code

        # Send the data
        self.publisher.send_json(code_data)
    def open_new_terminal(self) -> bool:
        """Create an interactive terminal session with proper error handling"""
        try:
            import pty
            import termios

            # Create a pseudoterminal pair
            master, slave = pty.openpty()

            # Get the slave name
            slave_name = os.ttyname(slave)

            # Set terminal settings
            term_settings = termios.tcgetattr(slave)
            term_settings[3] = term_settings[3] & ~termios.ECHO  # Disable echo
            termios.tcsetattr(slave, termios.TCSADRAIN, term_settings)

            # Simple environment
            env = os.environ.copy()
            env["TERM"] = "xterm"
            env["PS1"] = "$ "

            # Open an interactive shell in a new terminal window
            if platform.system() == "Darwin":  # macOS
                self.terminal_process = subprocess.Popen(
                    ['osascript', '-e', f'tell app "Terminal" to do script "tty {slave_name} && exec /bin/bash"'],
                    env=env
                )
            elif platform.system() == "Linux":
                self.terminal_process = subprocess.Popen(
                    ['gnome-terminal', '--', 'bash', '-c', f'tty {slave_name} && exec /bin/bash'],
                    env=env
                )
            else:  # Windows would need a different approach
                raise NotImplementedError("Windows not yet supported")

            # Store file descriptors
            self.master_fd = master
            self.slave_fd = slave

            # Create file objects
            self.terminal_stdin = os.fdopen(master, 'wb', buffering=0)
            self.terminal_stdout = os.fdopen(master, 'rb', buffering=0)
            self.terminal_stderr = self.terminal_stdout

            # Initialize and start the monitor
            self.monitor = ProcessMonitor(self)
            self.monitor.start_monitoring()
            return True

        except Exception as e:
            print(f"Error creating terminal session: {e}")
            traceback.print_exc()
            return False
    def read_terminal_output(self) -> List[str]:
        """Read output from terminal with proper error checking"""
        if not self.terminal_stdout:
            print("Terminal stdout not available")
            return []

        output = []
        try:
            while True:
                line = self.terminal_stdout.readline()
                if not line:
                    break
                output.append(line)
                # Send through ZMQ
                self.publisher.send_json({
                    'type': 'terminal_output',
                    'data': line,
                    'timestamp': time.time()
                })
        except Exception as e:
            print(f"Error reading terminal output: {e}")

        return output
    def is_terminal_active(self) -> bool:
        """Check if terminal session is active and valid"""
        return (self.terminal_process is not None and
                self.terminal_stdin is not None and
                self.terminal_stdout is not None and
                self.terminal_process.poll() is None)
    def monitor_terminal(self):
        """Monitor terminal activity continuously"""
        while self.is_terminal_active():
            self.read_terminal_output()
    def send_to_terminal(self, command: str) -> Optional[str]:
        """Send a command to the terminal with proper error checking"""
        if not self.terminal_stdin:
            print("Terminal session not properly initialized")
            return None

        try:
            # Ensure command ends with newline
            if not command.endswith('\n'):
                command += '\n'

            # Write command as bytes
            self.terminal_stdin.write(command.encode())
            self.terminal_stdin.flush()

            # No need to read response here as the monitor will catch it
            return "Command sent"
        except Exception as e:
            print(f"Error sending to terminal: {e}")
            return None


class Zapper:
    term_sesh : Optional[TermSesh] = None
    subscriber_thread : Optional[threading.Thread]
    def __init__(self, port=5555):
        self.context = zmq.Context()
        self.subscriber = self.context.socket(zmq.SUB)
        self.subscriber.connect(f"tcp://127.0.0.1:{port}")
        self.subscriber.setsockopt_string(zmq.SUBSCRIBE, "")
        self.system = platform.system()
        self.running = False
        self.subscriber_thread = None

    def start(self):
        """Start the subscriber thread"""
        self.running = True
        self.subscriber_thread = threading.Thread(target=self.run_subscriber)
        self.subscriber_thread.daemon = True
        self.subscriber_thread.start()
        print("ZMQ subscriber thread started")
    def run_subscriber(self):
        while self.running:
            try:
                message = self.subscriber.recv_json(flags=zmq.NOBLOCK)
                print(f"new message received: {message}")
            except zmq.Again:
                time.sleep(0.1)
            except Exception as e:
                print(f"Error receiving message: {e}")
                time.sleep(0.1)

    def stop(self):
        """Stop subscriber threads"""
        self.running = False
        if self.subscriber_thread:
            self.subscriber_thread.join()

class ProcessMonitor:
    def __init__(self, term_sesh: TermSesh):
        self.term_sesh = term_sesh
        self.stdin_thread = None
        self.stdout_thread = None
        self.stderr_thread = None
        self.is_running = False
        self.poll_interval = 0.1

    def start_monitoring(self):
        """Start monitoring stdout and stderr in separate threads"""
        if not self.term_sesh or not self.term_sesh.terminal_process:
            print("No terminal process to monitor")
            return False


        if not self.term_sesh.terminal_stdin or not self.term_sesh.terminal_stdout or not self.term_sesh.terminal_stderr:
            print("No stdout/stderr streams available")
            return False

        self.is_running = True
        self.stdin_thread = threading.Thread(target=self._monitor_stdin)
        self.stdout_thread = threading.Thread(target=self._monitor_stdout)
        self.stderr_thread = threading.Thread(target=self._monitor_stderr)

        self.stdin_thread.daemon=True
        self.stdout_thread.daemon = True
        self.stderr_thread.daemon = True
        self.stdin_thread.start()
        print('stdin thread started')
        self.stdout_thread.start()
        print('stdout thread started')
        self.stderr_thread.start()
        print('stderr thread started')
        return True
    def _monitor_stdin(self):
        """Monitor stdout using non-blocking reads"""
        while self.is_running and self.term_sesh.is_terminal_active():
            try:
                # Use select to check if data is available
                if self.term_sesh.terminal_process and self.term_sesh.terminal_stdin and select.select([self.term_sesh.terminal_stdin], [], [], 0)[0]:
                    line = self.term_sesh.terminal_stdin.readline()
                    if line:
                        self.term_sesh.publisher.send_json({
                            'type': 'stdout',
                            'data': line.strip(),
                            'pid': self.term_sesh.terminal_process.pid,
                            'timestamp': time.time()
                        })
            except Exception as e:
                print(f"Error in stdout monitoring: {e}")
            time.sleep(self.poll_interval)

    def _monitor_stdout(self):
        """Monitor stdout using non-blocking reads"""

        # Pattern to remove ANSI escape sequences
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

        while self.is_running and self.term_sesh.is_terminal_active():
            print('monitoring stdout')
            try:
                # Try to read from the master fd
                data = os.read(self.term_sesh.master_fd, 1024)
                if data:
                    # Decode and clean the output
                    text = data.decode('utf-8', errors='ignore')
                    cleaned_text = ansi_escape.sub('', text)
                    # Remove control chars except newline/tab
                    cleaned_text = "".join(ch for ch in cleaned_text
                                         if ch.isprintable() or ch in '\n\t')

                    if cleaned_text.strip():
                        self.term_sesh.publisher.send_json({
                            'type': 'stdout',
                            'data': cleaned_text.strip(),
                            'pid': self.term_sesh.terminal_process.pid,
                            'timestamp': time.time()
                        })
            except BlockingIOError:
                # No data available right now
                time.sleep(self.poll_interval)
            except Exception as e:
                print(f"Error in stdout monitoring: {e}")
                break

    def _monitor_stderr(self):
        """Monitor stderr and send updates through ZMQ"""
        while self.is_running and self.term_sesh.is_terminal_active():
            try:
                import select
                if self.term_sesh.terminal_process and self.term_sesh.terminal_stderr and select.select([self.term_sesh.terminal_stderr], [], [], 0)[0]:
                    line = self.term_sesh.terminal_stderr.readline()
                    if line:
                        self.term_sesh.publisher.send_json({
                            'type': 'stderr',
                            'data': line.strip(),
                            'pid': self.term_sesh.terminal_process.pid,
                            'timestamp': time.time()
                        })
            except Exception as e:
                print(f"Error in stderr monitoring: {e}")
            time.sleep(self.poll_interval)


#if __name__ == "__main__":
