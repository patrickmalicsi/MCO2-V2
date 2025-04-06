import threading
import struct
import time
import socket
from sip_client import SIPClient
from rtp_sender import RTPSender

class RTCPSender:
    def __init__(self, remote_ip, remote_port):
        self.remote_ip = remote_ip
        self.remote_port = remote_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.packet_count = 0
        self.byte_count = 0

    def send_report(self):
        while True:
            # Construct RTCP Sender Report
            rtcp_header = struct.pack('!BBH', 0x80, 200, 6)  # Version 2, SR packet type
            sender_info = struct.pack('!IIIIII', 12345, int(time.time()), 0, self.packet_count, self.byte_count, 0)
            rtcp_packet = rtcp_header + sender_info

            # Send RTCP packet
            self.sock.sendto(rtcp_packet, (self.remote_ip, self.remote_port))
            print("RTCP Sender Report sent.")

            # Wait 5 seconds before sending the next report
            time.sleep(5)

def main():
    # Prompt the user to input the audio file name
    audio_file = input("Enter the name of the .wav file to play (e.g., audio.wav): ")

    # Use localhost for testing
    sip_client = SIPClient(local_ip="127.0.0.1", local_port=5060, remote_ip="127.0.0.1", remote_port=5061)
    rtp_sender = RTPSender(audio_file=audio_file, remote_ip="127.0.0.1", remote_port=5004)
    rtcp_sender = RTCPSender(remote_ip="127.0.0.1", remote_port=5005)

    try:
        # Start SIP call
        print("Starting SIP call...")
        sip_client.start_call()
        print("SIP call established.")

        # Start RTCP Sender in a separate thread
        rtcp_thread = threading.Thread(target=rtcp_sender.send_report, daemon=True)
        rtcp_thread.start()

        # Send RTP audio
        print(f"Sending RTP audio from file: {audio_file}...")
        rtp_sender.send_audio()
        print("RTP audio transmission complete.")

    except FileNotFoundError:
        print(f"Error: Audio file '{audio_file}' not found.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # End SIP call
        print("Ending SIP call...")
        sip_client.end_call()
        print("SIP call terminated.")

if __name__ == "__main__":
    main()