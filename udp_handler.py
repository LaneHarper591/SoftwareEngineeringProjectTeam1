import socket

class UdpHandler:
    def __init__(self, listen_ip="0.0.0.0", listen_port=7501, buffer_size=1024):
        self.listen_ip = listen_ip
        self.listen_port = listen_port
        self.buffer_size = buffer_size

        self.sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.sock.bind((self.listen_ip, self.listen_port))
        self.sock.setblocking(False)

        print(f"UDP server up and listening on {self.listen_ip}:{self.listen_port}")
    
    def poll(self):
        #Call once per fram (inside m.update()). 
        try:
            data, addr = self.sock.recvfrom(self.buffer_size)
            msg = data.decode("utf-8", errors="ignore")
            #echo for debugging
            self.sock.sendto(b"Hello UDP Client", addr)
            return msg,addr
        except BlockingIOError:
            return None,None
        
    def close(self):
        self.sock.close()
