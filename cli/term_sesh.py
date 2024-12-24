from process_monitor import ProcessMonitor
from typing import Optional
import zmq
import platform
import base64
import zlib
import subprocess
import traceback
import time
import threading


class TermSesh:
    monitor: Optional[ProcessMonitor]
    def __init__(self, port=5555, terminal_app=None, session_name='zapper_session'):
        self.context = zmq.Context()
        self.publisher = self.context.socket(zmq.PUB)
        self.publisher.bind(f"tcp://*:{port}")
        self.system = platform.system()
        self.session_name = session_name
        self.terminal_process = None
        self.monitor = None
        self.tmux_stack = []


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

    def open_new_terminal(self):
        """Create an interactive terminal session with proper error handling"""
        try:
            self.kill_tmux_session()

            subprocess.run(['tmux', 'new-session', '-d', '-s', self.session_name])

                        # Open a new terminal window and attach to the tmux session
            if platform.system() == "Darwin":  # macOS
                apple_script = f'''
                    tell application "Terminal"
                        do script "tmux attach-session -t {self.session_name}"
                    end tell
                '''
                subprocess.Popen(['osascript', '-e', apple_script])
            elif platform.system() == "Linux":
                subprocess.Popen([
                    'gnome-terminal', '--', 'tmux', 'attach-session', '-t', self.session_name
                ])
            else:
                raise NotImplementedError("Windows not yet supported")

            # Allow some time for tmux session to start
            time.sleep(1)

            return True
        except Exception as e:
            print(f"Error creating tmux session: {e}")
            traceback.print_exc()
            return False

    def kill_tmux_session(self):
        """Kill the tmux session if it exists"""
        try:
            # Check if session exists
            result = subprocess.run(
                ['tmux', 'has-session', '-t', self.session_name],
                capture_output=True
            )
            if result.returncode == 0:  # Session exists
                subprocess.run(['tmux', 'kill-session', '-t', self.session_name])
                print(f"Killed tmux session: {self.session_name}")
        except Exception as e:
            print(f"Error killing tmux session: {e}")

    def read_tmux_output(self):
        """Read output from the tmux session"""
        try:
            result = subprocess.run(['tmux', 'capture-pane', '-t', self.session_name, '-p'], capture_output=True, text=True)
            if result.stdout:
                cleaned_output = self.clean_tmux_output(result.stdout)
                if len(self.tmux_stack) == 0 or cleaned_output != self.tmux_stack[-1]:
                    self.tmux_stack.append(cleaned_output)
                    print(self.tmux_stack[-1])
                    return self.tmux_stack[-1]
            return ""
        except Exception as e:
            print(f"Error reading tmux session: {e}")
            return ""

    def clean_tmux_output(self, raw_output: str) -> str:
        """Clean and format tmux output by removing ANSI escape sequences and extra whitespace"""
        import re

        # Remove ANSI escape sequences
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        # Remove unicode characters commonly used in prompts
        unicode_chars = re.compile(r'[\ue0b0-\ue0b3\ue5ff\ue615\ue606\uf48a\uf489\ue0a0]')

        # Clean the output
        cleaned = ansi_escape.sub('', raw_output)
        cleaned = unicode_chars.sub('', cleaned)

        # Split into lines and remove empty lines
        lines = [line.strip() for line in cleaned.split('\n')]
        lines = [line for line in lines if line]

        # Remove duplicate consecutive lines
        unique_lines = []
        prev_line = None
        for line in lines:
            if line != prev_line:
                unique_lines.append(line)
                prev_line = line

        return '\n'.join(unique_lines)
    def is_terminal_active(self) -> bool:
        """Check if terminal session is active and valid"""
        return (self.terminal_process is not None and
                self.terminal_process.poll() is None)
    def send_to_terminal(self, command: str) -> Optional[str]:
        """Send a command to the tmux session"""
        try:
            subprocess.run(['tmux', 'send-keys', '-t', self.session_name, command, 'C-m'])
            return "Command sent"
        except Exception as e:
            print(f"Error sending to tmux session: {e}")
            return None
