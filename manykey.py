#!/bin/python
"""
ManyKey Writer
"""

import wx
import wx.stc
import webbrowser
from pubsub import pub
from serial_helpers import *

VERSION = "0.1.1 (Alpha)"

class GuiFrame(wx.Frame):
    def __init__(self, *args, **kw):
        super(GuiFrame, self).__init__(*args, **kw)

        self.switch_count = 0
        self.max_keys = 0
        self.switch_text_boxes = []
        self.current_device = None
        self.devices = {}
        self.line_count = None

        pub.subscribe(self.serial_callback, "serial")

        self.CreateStatusBar()
        self.main_panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)


        # Select Device Title
        select_device = wx.StaticText(self.main_panel, label="Connect to Device")
        font = select_device.GetFont()
        font.PointSize -= 0
        font = font.Bold()
        select_device.SetFont(font)
        main_sizer.Add(select_device, proportion=0, flag=wx.ALL, border=5)


        # Device Selection
        device_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.device_select = wx.Choice(self.main_panel, choices=[])
        self.device_select.Bind(wx.EVT_CHOICE, self.select_device)
        device_sizer.Add(self.device_select, proportion=3, flag=wx.ALL, border=5)
        device_refresh_button = wx.Button(self.main_panel, label='Refresh Devices')
        device_refresh_button.Bind(wx.EVT_BUTTON, self.refresh_devices)
        device_sizer.Add(device_refresh_button, proportion=1, flag=wx.ALL, border=5)        
        main_sizer.Add(device_sizer, proportion=0, flag=wx.EXPAND)
        self.refresh_devices(None)


        # Keys Title
        select_keys = wx.StaticText(self.main_panel, label="Set Keys")
        font = select_keys.GetFont()
        font.PointSize -= 0
        font = font.Bold()
        select_keys.SetFont(font)
        main_sizer.Add(select_keys, proportion=0, flag=wx.ALL, border=5)


        # Key Selection Panel
        self.keys_edit = wx.stc.StyledTextCtrl(self.main_panel)
        self.keys_edit.SetMarginWidth(1, 55)
        self.keys_edit.StyleSetFont(1, self.keys_edit.StyleGetFont(0))
        self.keys_edit.SetMarginType(1, wx.stc.STC_MARGIN_RTEXT)
        self.keys_edit.SetMarginCursor(1, 0)
        self.keys_edit.SetMarginLeft(5)
        self.keys_edit.SetScrollWidth(5)
        self.keys_edit.SetScrollWidthTracking(True)
        self.keys_edit.Bind(wx.stc.EVT_STC_CHANGE, self.update_margins)
        main_sizer.Add(self.keys_edit, proportion=1, flag=wx.ALL | wx.EXPAND, border=5)


        # Controls
        controls_sizer = wx.BoxSizer(wx.HORIZONTAL)
        clear_button = wx.Button(self.main_panel, label='Clear')
        clear_button.Bind(wx.EVT_BUTTON, self.clear_keys)
        controls_sizer.Add(clear_button, proportion=1, flag=wx.ALL, border=5)
        self.read_button = wx.Button(self.main_panel, label='Read')
        self.read_button.Bind(wx.EVT_BUTTON, self.read_device_keys)
        controls_sizer.Add(self.read_button, proportion=1, flag=wx.ALL, border=5)
        self.write_button = wx.Button(self.main_panel, label='Write')
        self.write_button.Bind(wx.EVT_BUTTON, self.write_keys)
        controls_sizer.Add(self.write_button, proportion=1, flag=wx.ALL, border=5)
        main_sizer.Add(controls_sizer, proportion=0, flag=wx.EXPAND)


        self.main_panel.SetSizer(main_sizer)
        # main_sizer.Fit(self.main_panel)


        self.make_menu_bar()
        self.clear_keys(None)
        self.SetStatusText("No device connected")
        self.disconnect_device()


    def disconnect_device(self):
        self.write_button.Disable()
        self.read_button.Disable()
        self.current_device = None


    def refresh_devices(self, event):
        self.SetStatusText("No device connected")
        self.devices = {}
        self.current_device = None
        self.device_select.Clear()
        self.device_select.Append("Select a Device")
        SerialDevicesHelper()


    def select_device(self, event):
        try:
            self.disconnect_device()
            device = self.devices[self.device_select.GetStringSelection()]
            self.current_device = device
            self.SetStatusText("Connecting to {}...".format(device))
            SerialDeviceQueryHelper(device)

        except KeyError:
            self.SetStatusText("No device connected")
            self.disconnect_device()


    def read_device_keys(self, event):
        SerialDeviceReadHelper(self.current_device, self.switch_count)


    def clear_keys(self, event):
        newlines = []
        for index in range(0, self.switch_count - 1):
            newlines.append("\n")
        self.keys_edit.SetText("".join(newlines))


    def write_keys(self, event):
        SerialDeviceWriteHelper(self.current_device, self.keys_edit.GetValue(), self.switch_count, self.max_keys)


    def update_margins(self, event):
        lc = self.keys_edit.GetLineCount()
        if lc != self.line_count:
            self.line_count = lc
            for line in range(0, lc):
                self.keys_edit.MarginSetText(line, "Switch {}".format(line))
                self.keys_edit.MarginSetStyle(line, 1)
        # hacky way to shrink the horizontal scrollbar back down when line length decreases
        self.keys_edit.SetScrollWidth(5) 


    def make_menu_bar(self):
        helpMenu = wx.Menu()
        aboutItem = helpMenu.Append(wx.ID_ABOUT)
        websiteItem = helpMenu.Append(10000, "Visit ManyKey.org for Documentation")
        menuBar = wx.MenuBar()
        menuBar.Append(helpMenu, "&Help")
        self.SetMenuBar(menuBar)
        self.Bind(wx.EVT_MENU, self.on_about, aboutItem)
        self.Bind(wx.EVT_MENU, self.launch_website, websiteItem)


    def on_about(self, event):
        wx.MessageBox("Version {}\nManyKey.org".format(VERSION),
                      "ManyKey Writer",
                      wx.OK|wx.ICON_INFORMATION)


    def launch_website(self, event):
        webbrowser.open("https://www.manykey.org", new=2)


    def serial_callback(self, class_name, data):
        if class_name == 'ConnectionError':
            self.SetStatusText("Connection error occured")
            d = wx.MessageDialog(self, "Please check your device and try again", "An Error Occurred", wx.OK | wx.ICON_ERROR)
            d.ShowModal()
            d.Destroy()
        elif class_name == 'SerialDevicesHelper':
            self.devices = data
            for label in data.keys():
                self.device_select.Append(label)
        elif class_name == 'SerialDeviceQueryHelper':
            self.switch_count = data['switch_count']
            self.max_keys = data['max_keys']
            self.write_button.Enable()
            self.read_button.Enable()
            self.SetStatusText("Connected ({} switches, {} keys per switch)".format(self.switch_count, self.max_keys))  
            if self.keys_edit.CountCharacters(0,100) == 0:
                SerialDeviceReadHelper(self.current_device, self.switch_count)
        elif class_name == 'SerialDeviceReadHelper':
            self.keys_edit.SetText(data)
            self.SetStatusText("Connected ({} switches, {} keys per switch)".format(self.switch_count, self.max_keys))
        elif class_name == 'SerialDeviceWriteHelper':
            self.read_device_keys(None)
            d = wx.MessageDialog(self, "New key configuration was saved to device", "Successfully Wrote Keys", wx.OK | wx.ICON_NONE )
            d.ShowModal()
            d.Destroy()


if __name__ == '__main__':
    app = wx.App()
    frm = GuiFrame(None, title='ManyKey Writer', size=(400,300))
    frm.Show()
    app.MainLoop()
