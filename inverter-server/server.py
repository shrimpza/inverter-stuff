import socket
import threading
import struct
import time

BUF_SIZE = 1152

msg_start = 0xa5
msg_end = 0x15
meta_len = 13

def start_server(host, port):
    print(f"[STARTING] Server is starting at {host}:{port}")
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen()

    while True:
        conn, addr = server_socket.accept()
        conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        print(f"[ACCEPTED CONNECTION] {addr} connected.")

        # Spawn a new thread to handle the client connection
        client_thread = threading.Thread(target=handle_client, args=(conn, addr))
        client_thread.start()

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")

    while True:
        data = conn.recv(BUF_SIZE)
        if not data:
            print(f"[CLOSED] [{addr}] Connection closed.")
            conn.close()
            return

        # message = data.decode()
        print(f"[RECV] [{addr}] ({len(data)}) {data.hex()}")

        message = Msg(data)

        response = message.response()

        print(f"[SEND] [{addr}] ({len(response)}) {response.hex()}")

        # send the response
        conn.sendall(response)

class Msg:

    def __init__(self, payload):
        self.data = payload
        self.length = struct.unpack("<H", payload[1:3])[0]
        
        expected_length = meta_len + self.length

        if (len(payload) != expected_length):
            raise Exception(f"Invalid payload length in message, expecting {len(payload-meta_len)} but was {self.length}")
        if (payload[0] != msg_start) or (payload[len(payload) - 1] != msg_end):
            raise Exception("Payload contains invalid start or end values")
        if payload[len(payload) - 2] != Msg.checksum(payload):
            raise Exception(f"Payload contains invalid checksum, expecting {Msg.checksum(payload)} but was {payload[frame_len - 2]}")
        
        self.control_code = payload[3:5]
        self.sequence = int.from_bytes(payload[5:7], byteorder="little") #payload[5]
        self.serial = int.from_bytes(payload[7:11], byteorder="little")
        self.frame_type = payload[11]
    
    def response(self):
        # response =
        # - start
        # - length
        # - control code
        # - sequence
        # - serial
        # - frame type
        # - sensor type
        # - current time
        # - checksum
        # - end
        
        # the control code on responses always seems to follow pattern:
        # req: 1043, res: 1013; 1042 -> 1012; 1047 -> 1017, etc
        # ! this is a huge hack !
        control_code = bytearray(
            self.control_code[0:1] +
            bytes.fromhex(str(max(10, int(self.control_code[1:2].hex())-30)))
        )

        # create payload containing "sensor type" 01 and the current time 
        timestamp = int(time.time())
        payload = bytearray(
            bytes([self.frame_type, 0x01]) +
            struct.pack('<I', timestamp) +
            bytes([0x78, 0x00, 0x00, 0x00])
        )
        
        res = bytearray(
            bytes([msg_start]) +
            struct.pack("<H", len(payload)) +
            control_code +
            struct.pack('<H', self.sequence + 1) +
            struct.pack('<I', self.serial) + 
            payload +
            bytes([0]) + # checksum placeholder
            bytes([msg_end])
        )
        res[len(res)-2] = Msg.checksum(res)
        return res
    
    @staticmethod
    def checksum(data):
        checksum = 0
        for i in range(1, len(data) - 2, 1):
            checksum += data[i] & 0xFF
        return int(checksum & 0xFF)

if __name__ == '__main__':
    start_server('0.0.0.0', 10000)


