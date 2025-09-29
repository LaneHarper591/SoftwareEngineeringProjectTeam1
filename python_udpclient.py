import socket, time
from typing import Optional

START_GAME_CODE = 202
END_GAME_CODE = 221
DEFAULT_TX_PORT = 7500

class PythonUdpClient:
    def __init__(self, dest_ip="127.0.0.1", dest_port=DEFAULT_TX_PORT, enable_broadcast=False):
        self.dest_ip= dest_ip
        self.dest_port = dest_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.  setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if enable_broadcast:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def set_destination(self, dest_ip: str, dest_port: Optional[int] = None):
        self.dest_ip = dest_ip
        if dest_port is not None:
            self.dest_port = dest_port

    def send_int(self, code: int) -> bool:
        try:
            payload = str(int(code)).encode("utf-8")
            self.sock.sendto(payload, (self.dest_ip, self.dest_port))
            return True
        except Exception as e:
            print(f"[python_udpclient] send error: {e}")
            return False
        
    def start_game(self) -> bool:
        return self.send_int(START_GAME_CODE)
    
    def end_game(self, repeats: int = 3, interval_s: float = 0.05) -> bool:
        ok = True
        for _ in range(repeats):
            ok = self.send_int(END_GAME_CODE) and ok
            if interval_s > 0:
                time.sleep(interval_s)
            return ok

def close(self):
    if hasattr(self, "sock") and self.sock:
        try:
            self.sock.close()
        except OSError as e:
            print(f"[python_udpclient] close error: {e}")


