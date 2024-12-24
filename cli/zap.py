# auto_debugger.py
import time
import zmq
import threading

#from relational import relational_error_parsing_function

class Zapper:
    def __init__(self, port=5555):
        self.context = zmq.Context()
        self.running = False
        self.subscriber_thread = None

    def start(self):
        """Start the publisher thread"""
        self.running = True
        self.subscriber_thread = threading.Thread(target=self.run_subscriber)
        self.subscriber_thread.daemon = True
        self.subscriber_thread.start()
        print("ZMQ publisher thread started")

    def run_subscriber(self):
        while self.running:
            try:
                # Implement subscriber logic if needed
                pass
            except Exception as e:
                print(f"Error in Zapper subscriber: {e}")
            time.sleep(0.1)

    def stop(self):
        """Stop publisher threads"""
        self.running = False
        if self.subscriber_thread:
            self.subscriber_thread.join()
        self.context.term()



#if __name__ == "__main__":
