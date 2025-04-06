import socket
import wave
import struct
import pyaudio

class RTPReceiver:
    def __init__(self, local_port):
        self.local_port = local_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
        self.sock.bind(("", self.local_port))

    def parse_rtp_header(self, data):
        # RTP header is 12 bytes long
        header = struct.unpack('!BBHII', data[:12])
        payload = data[12:]  # Extract the payload (audio data)
        return payload

    def receive_audio(self):
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=8000, output=True)

        with wave.open("received_audio.wav", 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(8000)

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

            except Exception as e:
                print(f"Error: {e}")
            finally:
                self.sock.close()
                stream.stop_stream()
                stream.close()
                p.terminate()