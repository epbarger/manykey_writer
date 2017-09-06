import threading
import serial
import serial.tools.list_ports
import bidict
import time

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
    def __init__(self, gui):
        super(SerialDevicesHelper, self).__init__()
        self.gui = gui

    def run(self):
        self.gui.devices = {}
        self.gui.current_device = None
        self.gui.device_select.Clear()
        self.gui.device_select.Append("Select a Device")
        for index, port in enumerate(serial.tools.list_ports.comports()):
            device_label = "{} - {}".format(port.device, port.description)
            self.gui.devices[device_label] = port.device
            self.gui.device_select.Append(device_label)


class SerialDeviceQueryHelper(threading.Thread):
    def __init__(self, gui):
        super(SerialDeviceQueryHelper, self).__init__()
        self.gui = gui

    def run(self):
        serial_connection = serial.Serial()
        serial_connection.baudrate = 9600
        serial_connection.port = self.gui.current_device
        serial_connection.open()
        if serial_connection.is_open:
            serial_connection.write(bytearray([0xEE, 0x02, 0xFF]))

            response = []
            while (len(response) == 0 or response[-1] != b'\xff'):
                byte = serial_connection.read()
                response.append(byte)
            self.gui.switch_count = response[2][0]
            self.gui.max_keys = response[3][0]
            self.gui.write_button.Enable()
            self.gui.read_button.Enable()
            self.gui.SetStatusText("Connected ({} switches, {} keys per switch)".format(self.gui.switch_count, self.gui.max_keys))  
            
            if self.gui.keys_edit.CountCharacters(0,100) == 0:
                read_helper = SerialDeviceReadHelper(self.gui)
                read_helper.start()
                read_helper.join()
        else:
            self.gui.SetStatusText("Connection failed") 
        serial_connection.close()


class SerialDeviceReadHelper(threading.Thread):
    def __init__(self, gui):
        super(SerialDeviceReadHelper, self).__init__()
        self.gui = gui

    def run(self):
        serial_connection = serial.Serial()
        serial_connection.baudrate = 9600
        serial_connection.port = self.gui.current_device
        serial_connection.open()
        if serial_connection.is_open:
            keys_edit = []
            for switch_index in range(0, self.gui.switch_count):
                serial_connection.write(bytearray([0xEE, 0x00, switch_index, 0xFF]))
                response = []
                while (len(response) == 0 or response[-1] != b'\xff'):
                    byte = serial_connection.read()
                    response.append(byte)
                # print("read_response: {}".format(response))
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
            self.gui.keys_edit.SetText(keys_edit)
        else:
            self.gui.SetStatusText("Connection failed")
        serial_connection.close()


class SerialDeviceWriteHelper(threading.Thread):
    def __init__(self, gui):
        super(SerialDeviceWriteHelper, self).__init__()
        self.gui = gui

    def run(self):
        serial_connection = serial.Serial()
        serial_connection.baudrate = 9600
        serial_connection.port = self.gui.current_device
        serial_connection.open()
        if serial_connection.is_open:
            key_lines = self.gui.keys_edit.GetValue().splitlines()
            while len(key_lines) < self.gui.switch_count:
                key_lines.append('')
            for index, key_list in enumerate(key_lines):
                serial_request = [0xEE, 0x01, index]
                for index, key in enumerate(key_list.split()):
                    if index >= self.gui.max_keys:
                        break

                    if len(key) > 1:
                        try:
                            serial_request.append(KEY_TO_HEX_BIDICT[key])
                        except KeyError:
                            continue
                    elif ord(key) >= 33 and ord(key) <= 126:
                        serial_request.append(ord(key))
                    # else:
                        # print("unrecognized character")
                serial_request.append(0xFF)
                serial_connection.write(bytearray(serial_request))
                # print("write {}".format(serial_request))
                time.sleep(0.1)
                serial_connection.reset_input_buffer()

            read_helper = SerialDeviceReadHelper(self.gui)
            read_helper.start()
            read_helper.join()
        else:
            self.gui.SetStatusText("Connection failed") 
        serial_connection.close()
