import socket
import uuid

class SIPClient:
    def __init__(self, local_ip, local_port, remote_ip, remote_port):
        self.local_ip = local_ip
        self.local_port = local_port
        self.remote_ip = remote_ip
        self.remote_port = remote_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.local_ip, self.local_port))
        self.call_id = str(uuid.uuid4())  # Generate a unique Call-ID

    def receive_call(self):
        while True:
            message, addr = self.sock.recvfrom(1024)
            if b"INVITE" in message:
                # SDP Body
                sdp_body = f"v=0\r\n"
                sdp_body += f"o=- 0 0 IN IP4 {self.local_ip}\r\n"
                sdp_body += f"s=VoIP Call\r\n"
                sdp_body += f"c=IN IP4 {self.local_ip}\r\n"
                sdp_body += f"t=0 0\r\n"
                sdp_body += f"m=audio {self.local_port} RTP/AVP 0\r\n"
                sdp_body += f"a=rtpmap:0 PCMU/8000\r\n"

                # 200 OK Response
                response = f"SIP/2.0 200 OK\r\n"
                response += f"Via: SIP/2.0/UDP {self.local_ip}:{self.local_port}\r\n"
                response += f"To: <sip:{self.local_ip}:{self.local_port}>\r\n"
                response += f"From: <sip:{self.remote_ip}:{self.remote_port}>\r\n"
                response += f"Call-ID: {self.call_id}\r\n"
                response += "CSeq: 1 200 OK\r\n"
                response += "Content-Type: application/sdp\r\n"
                response += f"Content-Length: {len(sdp_body)}\r\n\r\n"
                response += sdp_body
                self.sock.sendto(response.encode(), addr)

            if b"ACK" in message:
                print("ACK received. Call established.")
                break

    def end_call(self):
        # BYE Message
        bye_message = f"BYE sip:{self.remote_ip}:{self.remote_port} SIP/2.0\r\n"
        bye_message += f"Via: SIP/2.0/UDP {self.local_ip}:{self.local_port}\r\n"
        bye_message += f"To: <sip:{self.remote_ip}:{self.remote_port}>\r\n"
        bye_message += f"From: <sip:{self.local_ip}:{self.local_port}>\r\n"
        bye_message += f"Call-ID: {self.call_id}\r\n"
        bye_message += "CSeq: 2 BYE\r\n"
        bye_message += "Content-Length: 0\r\n\r\n"
        self.sock.sendto(bye_message.encode(), (self.remote_ip, self.remote_port))
        self.sock.close()