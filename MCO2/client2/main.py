from sip_client import SIPClient
from rtp_receiver import RTPReceiver
import socket
import struct
import time
import threading

class RTCPReceiver:
    def __init__(self, remote_ip, remote_port):
        self.remote_ip = remote_ip
        self.remote_port = remote_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.packet_count = 0
        self.running = True  # Add a flag to control the thread
        self.stop_event = threading.Event()  # Event to signal the thread to stop

    def send_report(self):
        while self.running:
            # Construct RTCP Receiver Report
            rtcp_header = struct.pack('!BBH', 0x80, 201, 7)  # Version 2, RR packet type
            report_block = struct.pack('!IIII', 12345, self.packet_count, 0, 0)
            rtcp_packet = rtcp_header + report_block

            # Send RTCP packet
            self.sock.sendto(rtcp_packet, (self.remote_ip, self.remote_port))
            print("RTCP Receiver Report sent.")

            # Wait for 5 seconds or until the stop event is set
            if self.stop_event.wait(5):  # Wait for 5 seconds or until stop_event is set
                break

    def stop(self):
        self.running = False  # Stop the thread
        self.stop_event.set()  # Wake up the thread if it's sleeping

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

        # Start RTCP Receiver in a separate thread
        rtcp_thread = threading.Thread(target=rtcp_receiver.send_report, daemon=True)
        rtcp_thread.start()

        # Receive RTP audio
        print("Receiving RTP audio...")
        rtp_receiver.receive_audio()
        print("RTP audio reception complete.")

        # Stop RTCP Receiver
        print("Stopping RTCP Receiver...")
        rtcp_receiver.stop()
        rtcp_thread.join()

    except Exception as e:
        print(f"Error: {e}")

    finally:
        # End SIP call
        print("Ending SIP call...")
        sip_client.end_call()
        print("SIP call terminated.")

if __name__ == "__main__":
    main()