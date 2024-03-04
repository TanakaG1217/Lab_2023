import serial
import serial.tools.list_ports


def check_serial_ports():
    ports = serial.tools.list_ports.comports()
    connected = []
    for port in ports:
        try:
            s = serial.Serial(port.device)
            s.close()
            connected.append(port.device)
        except (OSError, serial.SerialException):
            pass
    return connected


connected_ports = check_serial_ports()
print("接続されているシリアルポート:", connected_ports)
