import socket
import wave
import struct
import pyaudio
import time
import random

class RTPReceiver:
    def __init__(self, local_port, remote_ip, remote_port):
        self.local_port = local_port
        self.remote_ip = remote_ip
        self.remote_port = remote_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
        self.sock.bind(("", self.local_port))
        self.ssrc = random.randint(0, 2**32 - 1)  # Generate a random SSRC during initialization

    def parse_rtp_header(self, data):
        # RTP header is 12 bytes long
        header = struct.unpack('!BBHII', data[:12])
        payload = data[12:]  # Extract the payload (audio data)
        return payload

    def send_rtcp_receiver_report(self):
        try:
            # Construct a simple RTCP Receiver Report (RR) based on the received RTP data
            rtcp_header = struct.pack('!BBH', 0x80, 201, 6)  # Version 2, RR packet type
            report_block = struct.pack('!IIBBH', self.ssrc, 0, 0, 0, 0)  # Use dynamically generated SSRC
            rtcp_packet = rtcp_header + report_block

            # Send RTCP Receiver Report
            self.sock.sendto(rtcp_packet, (self.remote_ip, self.remote_port))
            print(f"RTCP Receiver Report sent. SSRC = {self.ssrc}")
        except Exception as e:
            print(f"Error sending RTCP Receiver Report: {e}")

    def receive_audio(self):
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=8000, output=True)

        with wave.open("received_audio.wav", 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(8000)

            packet_count = 0  # Counter for received RTP packets
            last_rtcp_time = time.time()  # Record the time of the last RTCP report sent

            try:
                while True:
                    data, _ = self.sock.recvfrom(2048)
                    if not data or data == b"END":  # Check for end-of-stream signal
                        print("End of RTP stream detected.")
                        break

                    # Parse RTP header and extract audio payload
                    payload = self.parse_rtp_header(data)

                    # Write audio payload to file
                    wf.writeframes(payload)

                    # Play audio in real-time
                    stream.write(payload)

                    packet_count += 1

                    # Send RTCP Receiver Report every 5 seconds
                    current_time = time.time()
                    if current_time - last_rtcp_time >= 5:
                        self.send_rtcp_receiver_report()
                        last_rtcp_time = current_time  # Reset the last RTCP report time

            except Exception as e:
                print(f"Error: {e}")
            finally:
                self.sock.close()
                stream.stop_stream()
                stream.close()
                p.terminate()

# Standalone function to parse RTCP packets
def parse_rtcp_packet(data):
    try:
        # Unpack the RTCP header (first 4 bytes)
        rtcp_header = struct.unpack('!BBH', data[:4])
        version = (rtcp_header[0] >> 6) & 0x03
        padding = (rtcp_header[0] >> 5) & 0x01
        report_count = rtcp_header[0] & 0x1F
        packet_type = rtcp_header[1]
        length = rtcp_header[2]

        print(f"RTCP Packet:")
        print(f"  Version: {version}")
        print(f"  Padding: {padding}")
        print(f"  Report Count: {report_count}")
        print(f"  Packet Type: {packet_type}")
        print(f"  Length: {length}")

        if packet_type == 200:  # Sender Report (SR)
            sender_ssrc = struct.unpack('!I', data[4:8])[0]
            print(f"  Sender SSRC: {sender_ssrc}")
        elif packet_type == 201:  # Receiver Report (RR)
            receiver_ssrc = struct.unpack('!I', data[4:8])[0]
            print(f"  Receiver SSRC: {receiver_ssrc}")
        else:
            print("  Unknown RTCP packet type.")
    except Exception as e:
        print(f"Error parsing RTCP packet: {e}")