import threading
import serial
import serial.tools.list_ports
import bidict
import time
import wx
from wx.lib.pubsub import pub

KEY_TO_HEX_BIDICT = bidict.orderedbidict({
    "LEFT_CTRL": 0x80,
    "LEFT_SHIFT": 0x81,
    "LEFT_ALT": 0x82,
    "LEFT_GUI": 0x83,
    "RIGHT_CTRL": 0x84,
    "RIGHT_SHIFT": 0x85,
    "RIGHT_ALT": 0x86,
    "RIGHT_GUI": 0x87,
    "UP_ARROW": 0xDA,
    "DOWN_ARROW": 0xD9,
    "LEFT_ARROW": 0xD8,
    "RIGHT_ARROW": 0xD7,
    "BACKSPACE": 0xB2,
    "TAB": 0xB3,
    "RETURN": 0xB0,
    "ESC": 0xB1,
    "INSERT": 0xD1,
    "DELETE": 0xD4,
    "PAGE_UP": 0xD3,
    "PAGE_DOWN": 0xD6,
    "HOME": 0xD2,
    "END": 0xD5,
    "CAPS_LOCK": 0xC1,
    "F1": 0xC2,
    "F2": 0xC3,
    "F3": 0xC4,
    "F4": 0xC5,
    "F5": 0xC6,
    "F6": 0xC7,
    "F7": 0xC8,
    "F8": 0xC9,
    "F9": 0xCA,
    "F10": 0xCB,
    "F11": 0xCC,
    "F12": 0xCD,
    "SPACE": 0x20,
})

class SerialDevicesHelper(threading.Thread):
    def __init__(self):
        super(SerialDevicesHelper, self).__init__()
        self.start()

    def run(self):
        try:
            result = {}
            for index, port in enumerate(serial.tools.list_ports.comports()):
                device_label = "{} - {}".format(port.device, port.description)
                result[device_label] = port.device
            wx.CallAfter(pub.sendMessage, "serial", class_name=type(self).__name__, data=result )
        except Exception:
            wx.CallAfter(pub.sendMessage, "serial", class_name="ConnectionError", data=None)


class SerialDeviceQueryHelper(threading.Thread):
    def __init__(self, port):
        super(SerialDeviceQueryHelper, self).__init__()
        self.port = port
        self.start()

    def run(self):
        try:
            result = { 'switch_count': None, 'max_keys': None }
            serial_connection = serial.Serial()
            serial_connection.baudrate = 9600
            serial_connection.port = self.port
            serial_connection.open()
            if serial_connection.is_open:
                serial_connection.write(bytearray([0xEE, 0x02, 0xFF]))
                response = []
                while (len(response) == 0 or response[-1] != b'\xff'):
                    byte = serial_connection.read()
                    response.append(byte)
                result['switch_count'] = response[2][0]
                result['max_keys'] = response[3][0]
                wx.CallAfter(pub.sendMessage, "serial", class_name=type(self).__name__, data=result)        
            else:
                raise Exception("serial_connection is closed")
            serial_connection.close()
        except Exception:
            wx.CallAfter(pub.sendMessage, "serial", class_name="ConnectionError", data=None)



class SerialDeviceReadHelper(threading.Thread):
    def __init__(self, port, switch_count):
        super(SerialDeviceReadHelper, self).__init__()
        self.port = port
        self.switch_count = switch_count
        self.start()

    def run(self):
        try:
            serial_connection = serial.Serial()
            serial_connection.baudrate = 9600
            serial_connection.port = self.port
            serial_connection.open()
            if serial_connection.is_open:
                keys_edit = []
                for switch_index in range(0, self.switch_count):
                    serial_connection.write(bytearray([0xEE, 0x00, switch_index, 0xFF]))
                    response = []
                    while (len(response) == 0 or response[-1] != b'\xff'):
                        byte = serial_connection.read()
                        response.append(byte)
                    converted_chars = []
                    for char in response[3:len(response)-1]:
                        if char[0] >= 33 and char[0] <= 126:
                            converted_chars.append(chr(char[0]))
                        else:
                            try:
                                converted_chars.append(KEY_TO_HEX_BIDICT.inv[char[0]])
                            except KeyError:
                                continue
                    if len(converted_chars) == 0:
                        keys_edit.append(" ")
                    else:
                        keys_edit.append(" ".join(converted_chars))
                        
                keys_edit = "\n".join(keys_edit)
                wx.CallAfter(pub.sendMessage, "serial", class_name=type(self).__name__, data=keys_edit)
            else:
                raise Exception("serial_connection is closed")
            serial_connection.close()
        except Exception:
            wx.CallAfter(pub.sendMessage, "serial", class_name="ConnectionError", data=None)


class SerialDeviceWriteHelper(threading.Thread):
    def __init__(self, port, keys_edit, switch_count, max_keys):
        super(SerialDeviceWriteHelper, self).__init__()
        self.port = port
        self.keys_edit = keys_edit
        self.switch_count = switch_count
        self.max_keys = max_keys
        self.start()

    def run(self):
        try:
            serial_connection = serial.Serial()
            serial_connection.baudrate = 9600
            serial_connection.port = self.port
            serial_connection.open()
            if serial_connection.is_open:
                key_lines = self.keys_edit.splitlines()
                while len(key_lines) < self.switch_count:
                    key_lines.append('')
                for index, key_list in enumerate(key_lines):
                    serial_request = [0xEE, 0x01, index]
                    for index, key in enumerate(key_list.split()):
                        if index >= self.max_keys:
                            break

                        if len(key) > 1:
                            try:
                                serial_request.append(KEY_TO_HEX_BIDICT[key])
                            except KeyError:
                                continue
                        elif ord(key) >= 33 and ord(key) <= 126:
                            serial_request.append(ord(key))

                    serial_request.append(0xFF)
                    serial_connection.write(bytearray(serial_request))
                    time.sleep(0.1)
                    serial_connection.reset_input_buffer()

                wx.CallAfter(pub.sendMessage, "serial", class_name=type(self).__name__, data=True)
            else:
                raise Exception("serial_connection is closed")
            serial_connection.close()
        except Exception:
            wx.CallAfter(pub.sendMessage, "serial", class_name="ConnectionError", data=None)

