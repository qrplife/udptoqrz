import io
import json
import socket
import struct
from qrz import QRZ
import random
from string import ascii_uppercase

listen_ip = "127.0.0.1"
listen_port = 2237  #2233
buffer_size = 1024

message_types=[
    "Heartbeat",
    "Status",
    "Decode",
    "Reply",
    "QSO Logged",
    "Close",
    "Replay",
    "Halt Tx",
    "Free Text",
    "WSPRDecode",
    "Location",
    "Logged ADIF",
    "Highlight Callsign",
    "SwtichConfiguration",
    "Configure"
]

class WSJTXMessage:
    def __init__(self, message_bytes,replay=False):
        mstream = io.BytesIO(message_bytes)
        self.magic_number = struct.unpack("!I",mstream.read(4))[0]
        self.schema_version = struct.unpack("!I",mstream.read(4))[0]
        self.msg_type = struct.unpack("!I",mstream.read(4))[0]
        self.unique_id_length = struct.unpack("!I",mstream.read(4))[0]
        self.unique_id = mstream.read(self.unique_id_length).decode('utf-8')
        try:
            self.decode(mstream)
        except Exception as ex:
            print(ex)
            if not replay:
                bin_file = f"{self.msg_type}_{self.unique_id}.bin"
                print(f"----- Saving bytes in {bin_file}")
                with open(f"{bin_file}",'wb') as capture_file:
                    capture_file.write(message_bytes)
        
    def read_string(self,mstream):
        length = struct.unpack("!I",mstream.read(4))[0]
        return mstream.read(length).decode('utf-8')

    def unpack(self,field_type,mstream):
        byte_order = "!"
        no_unpack = False
        if field_type == "uint8":
            fmt = byte_order + "H"
            no_unpack = True
            length = 1
        elif field_type == "int32":
            fmt = byte_order + "i"
            length = 4
        elif field_type == "bool":
            fmt = byte_order + "?"
            length = 1
        elif field_type == "uint32":
            fmt = byte_order + "I"
            length = 4
        elif field_type == "double":
            fmt = byte_order + "d"
            length = 8
        elif field_type == "int64":
            fmt = byte_order + "q"
            length = 8
        elif field_type == "uint64":
            fmt = byte_order + "Q"
            length = 8
        else:
            raise Exception(f"Unsupported unpack type: {field_type}")


        if no_unpack:
            value = int.from_bytes(mstream.read(length),'big')
        else:
            value = struct.unpack(fmt,mstream.read(length))[0]

        return value

    def decode(self,mstream):
        if self.msg_type == 0:
            self.maximum_schema_number = self.unpack("int32",mstream)
            self.version = self.read_string(mstream)
            self.revision = self.read_string(mstream)
        elif self.msg_type == 1:
            pass
        elif self.msg_type == 2:
            self.new = self.unpack("bool",mstream)
            self.time = self.unpack("uint32",mstream)
            self.snr = self.unpack("int32",mstream)
            self.delta_time = self.unpack("double",mstream)
            self.delta_frequency = self.unpack("int32",mstream)
            self.mode = self.read_string(mstream)
            self.message = self.read_string(mstream)
            self.low_confidence = self.unpack("bool",mstream)
            self.off_air = self.unpack("bool",mstream)
        elif self.msg_type == 3:
            pass
        elif self.msg_type == 4:
            pass
        elif self.msg_type == 5:
            self.date_off = self.unpack("int64",mstream)
            self.time_off = self.unpack("uint32",mstream)
            self.time_spec = self.unpack("uint8",mstream)
            if self.time_spec == 2:
                self.offset = self.unpack("int32",mstream)
            self.dx_call = self.read_string(mstream)
            self.dx_grid = self.read_string(mstream)
            self.tx_frequency = self.unpack("uint64",mstream)
            self.mode = self.read_string(mstream)
            self.report_sent = self.read_string(mstream)
            self.report_received = self.read_string(mstream)
            self.tx_power = self.read_string(mstream)
            self.comments = self.read_string(mstream)
            self.name = self.read_string(mstream)
            self.date_on = self.unpack("int64",mstream)
            self.time_on = self.unpack("uint32",mstream)
            self.time_spec = self.unpack("uint8",mstream)
            if self.time_spec == 2:
                self.offset = self.unpack("int32",mstream)
            self.operator_call = self.read_string(mstream)
            self.my_call = self.read_string(mstream)
            self.my_grid = self.read_string(mstream)
            self.exchange_sent = self.read_string(mstream)
            self.exchange_received = self.read_string(mstream)
            self.adif_propagation_mode = self.read_string(mstream)
        elif self.msg_type == 12:
            self.adif = self.read_string(mstream)

def listen_udp():
    UDP_server_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    UDP_server_socket.bind((listen_ip, listen_port))
    print(f"UDP server listening at {listen_ip} on port {listen_port} ...")
    qrz = QRZ("mycall")
    wsjtx_magic_number = b'\xad\xbc\xcb\xda'
    js8call_magic_number = b'{"pa'

    while(True):
        bytes_address_pair = UDP_server_socket.recvfrom(buffer_size)
        begin_message = bytes_address_pair[0][:4]
        if begin_message == wsjtx_magic_number: # Treat this as a WSJT-X message.
            message = WSJTXMessage(bytes_address_pair[0])        
            if message.msg_type == 0:
                print(f"WSJT-X version {message.version} {random.choice(ascii_uppercase)}")     
            
            if message.msg_type == 12:
                qrz.post_adif_log(message.adif)
                print(message.adif)

        elif begin_message == js8call_magic_number: # Treat this as a JS8Call message.
            message = json.loads(bytes_address_pair[0].decode('utf-8'))
            if message["type"] == "PING":
                print(f'{message["params"]["NAME"]} version {message["params"]["VERSION"]} {random.choice(ascii_uppercase)}')
            if message["type"] == "LOG.QSO":
                adif = message["value"]
                if "<eor>" not in adif: # Tack on the <eor> terminator if needed.
                    adif = adif + "<eor>"
                qrz.post_adif_log(adif)
                print(adif)
        else:
            print("Message sender not recognized as WSJT-X or JS8Call.")

if __name__ == "__main__":
    listen_udp()