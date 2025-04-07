import socket
import wave
import time
import struct
import random

class RTPSender:
    def __init__(self, audio_file, remote_ip, remote_port):
        self.audio_file = audio_file
        self.remote_ip = remote_ip
        self.remote_port = remote_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sequence_number = 0
        self.timestamp = 0
        self.ssrc = random.randint(0, 2**32 - 1)  # Generate a random SSRC to avoid SSRC collisions

    def build_rtp_header(self):
        # RTP Header: Version (2), Padding (0), Extension (0), CC (0), Marker (0), Payload Type (0)
        version = 2
        padding = 0
        extension = 0
        cc = 0
        marker = 0
        payload_type = 0
        header = (
            (version << 6) | (padding << 5) | (extension << 4) | cc,
            (marker << 7) | payload_type,
            self.sequence_number,
            self.timestamp,
            self.ssrc
        )
        # Pack the header into binary format
        return struct.pack('!BBHII', *header)

    def send_audio(self):
        try:
            with wave.open(self.audio_file, 'rb') as wf:
                frame_rate = wf.getframerate()
                frame_duration = 160 / frame_rate  # Assuming 160 samples per frame

                packet_count = 0  # Track the number of packets sent
                while True:
                    data = wf.readframes(160)
                    if not data:
                        break

                    # Build RTP packet
                    rtp_header = self.build_rtp_header()
                    rtp_packet = rtp_header + data

                    # Send RTP packet
                    self.sock.sendto(rtp_packet, (self.remote_ip, self.remote_port))

                    # Update sequence number and timestamp
                    self.sequence_number += 1
                    self.timestamp += 160  # Assuming 160 samples per frame

                    # Log sent packet
                    packet_count += 1
                    print(f"Sent RTP packet {packet_count}, timestamp {self.timestamp}")

                    # Simulate real-time streaming
                    time.sleep(frame_duration)

            # Send end-of-stream signal
            self.sock.sendto(b"END", (self.remote_ip, self.remote_port))
            print("End-of-stream signal sent.")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.sock.close()