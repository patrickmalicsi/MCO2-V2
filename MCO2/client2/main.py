from sip_client import SIPClient
from rtp_receiver import RTPReceiver
import socket
import struct
import time
import threading
import random

class RTCPReceiver:
    def __init__(self, remote_ip, remote_port):
        self.remote_ip = remote_ip
        self.remote_port = remote_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("", self.remote_port))  # Bind to the local port
        self.packet_count = 0
        self.running = True  # Add a flag to control the thread
        self.stop_event = threading.Event()  # Event to signal the thread to stop
        self.ssrc = random.randint(0, 2**32 - 1)  # Generate a random SSRC to avoid SSRC collisions

    def send_report(self):
        while self.running:
            try:
                # Construct RTCP Receiver Report
                rtcp_header = struct.pack('!BBH', 0x80, 201, 1)  # Version 2, RR packet type
                ssrc_sender = struct.pack('!I', self.ssrc)  # Use the dynamically generated SSRC
                rtcp_packet = rtcp_header + ssrc_sender

                # Log the packet details
                print(f"RTCP Receiver Report: SSRC = {self.ssrc}, Packet Count = {self.packet_count}")

                # Send RTCP packet
                self.sock.sendto(rtcp_packet, (self.remote_ip, self.remote_port))
                print(f"RTCP Receiver Report sent to {self.remote_ip}:{self.remote_port}")

                # Wait for 5 seconds or until the stop event is set
                if self.stop_event.wait(5):  # Wait for 5 seconds or until stop_event is set
                    print("RTCP Receiver thread stopping due to stop event.")
                    break
            except socket.error as e:
                print(f"Socket error in RTCP Receiver: {e}")
                self.running = False  # Stop the thread
            except Exception as e:
                print(f"Error in RTCP Receiver: {e}")
                break
        print("RTCP Receiver thread has exited.")

    def listen_for_reports(self):
        while self.running:
            try:
                # Listen for incoming RTCP packets
                data, addr = self.sock.recvfrom(1024)
                print(f"Received RTCP packet from {addr}: {data}")
            except socket.error as e:
                if not self.running:  # Ignore errors if the socket is closed intentionally
                    break
                print(f"Socket error in RTCP Receiver: {e}")
                break
            except Exception as e:
                print(f"Error in RTCP Receiver: {e}")
                break
        print("RTCP Receiver listening thread has exited.")

    def stop(self):
        print("RTCP Receiver stop() called.")
        self.running = False
        self.stop_event.set()  # Wake up any waiting threads
        if self.sock:
            self.sock.close()  # Close the socket
            self.sock = None

def main():
    # Use localhost for testing
    sip_client = SIPClient(local_ip="127.0.0.1", local_port=5061, remote_ip="127.0.0.1", remote_port=5060)
    rtp_receiver = RTPReceiver(local_port=5004)
    rtcp_receiver = RTCPReceiver(remote_ip="127.0.0.1", remote_port=5005)

    try:
        # Receive SIP call
        print("Waiting for SIP INVITE...")
        sip_client.receive_call()
        print("SIP call established.")

        # Start RTCP Receiver (sending and listening) in separate threads
        rtcp_send_thread = threading.Thread(target=rtcp_receiver.send_report, daemon=True)
        rtcp_listen_thread = threading.Thread(target=rtcp_receiver.listen_for_reports, daemon=True)
        rtcp_send_thread.start()
        rtcp_listen_thread.start()

        # Receive RTP audio
        print("Receiving RTP audio...")
        rtp_receiver.receive_audio()
        print("RTP audio reception complete.")

        # Stop RTCP Receiver
        print("Stopping RTCP Receiver...")
        rtcp_receiver.stop()
        rtcp_send_thread.join()
        rtcp_listen_thread.join()

    except Exception as e:
        print(f"Error: {e}")

    finally:
        # End SIP call
        print("Ending SIP call...")
        sip_client.end_call()
        print("SIP call terminated.")

if __name__ == "__main__":
    main()