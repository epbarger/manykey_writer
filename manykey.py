#!/bin/python
"""
ManyKey Writer
"""

import wx
import wx.stc
import serial
import serial.tools.list_ports
import threading
import bidict

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
	"SPACE": 0x32,
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
			# self.gui.updateKeysPanel()
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
		key_lines = self.gui.keys_edit.GetValue().splitlines()
		print(key_lines)

class GuiFrame(wx.Frame):
	def __init__(self, *args, **kw):
		# ensure the parent's __init__ is called
		super(GuiFrame, self).__init__(*args, **kw)
		self.CreateStatusBar()


		self.switch_count = 0
		self.max_keys = 0
		self.switch_text_boxes = []
		self.current_device = None
		self.devices = {}
		self.line_count = None

		# create a panel in the frame
		self.main_panel = wx.Panel(self)

		main_sizer = wx.BoxSizer(wx.VERTICAL)


		# Title Text / Logo
		title_sizer = wx.BoxSizer(wx.HORIZONTAL)
		title = wx.StaticText(self.main_panel, label="ManyKey Writer")
		font = title.GetFont()
		font.PointSize += 26
		font = font.Bold()
		title.SetFont(font)
		title_sizer.Add(title, proportion=0, flag=wx.ALL, border=5)
		main_sizer.Add(title_sizer, proportion=0, flag=wx.CENTER)


		# Horizontal Line
		main_sizer.Add(wx.StaticLine(self.main_panel), proportion=0, flag=wx.ALL|wx.EXPAND, border=5)


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
		self.device_select.Bind(wx.EVT_CHOICE, self.selectDevice)
		device_sizer.Add(self.device_select, proportion=4, flag=wx.ALL, border=5)
		device_refresh_button = wx.Button(self.main_panel, label='Refresh Devices')
		device_refresh_button.Bind(wx.EVT_BUTTON, self.updateDevices)
		device_sizer.Add(device_refresh_button, proportion=1, flag=wx.ALL, border=5)		
		main_sizer.Add(device_sizer, proportion=0, flag=wx.EXPAND)
		self.updateDevices(None)


		# Keys Title
		select_keys = wx.StaticText(self.main_panel, label="Set Keys")
		font = select_keys.GetFont()
		font.PointSize -= 0
		font = font.Bold()
		select_keys.SetFont(font)
		main_sizer.Add(select_keys, proportion=0, flag=wx.ALL, border=5)


		# Key Selection Panel
		# self.keys_panel = wx.Panel(self.main_panel)
		# main_sizer.Add(self.keys_panel, proportion=1, flag=wx.EXPAND)
		# self.updateKeysPanel()
		# self.keys_edit = wx.TextCtrl(self.main_panel, style=wx.TE_MULTILINE | wx.TE_DONTWRAP)
		self.keys_edit = wx.stc.StyledTextCtrl(self.main_panel)
		self.keys_edit.SetMarginWidth(1, 55)
		self.keys_edit.StyleSetFont(1, self.keys_edit.StyleGetFont(0))
		self.keys_edit.SetMarginType(1, wx.stc.STC_MARGIN_RTEXT) # wx.stc.STC_MARGIN_NUMBER)
		self.keys_edit.SetMarginCursor(1, 0)
		self.keys_edit.SetMarginLeft(5)
		self.keys_edit.SetScrollWidth(5)
		self.keys_edit.SetScrollWidthTracking(True)
		self.keys_edit.Bind(wx.stc.EVT_STC_CHANGE, self.updateMargins)



		main_sizer.Add(self.keys_edit, proportion=1, flag=wx.ALL | wx.EXPAND, border=5)

		# Controls
		controls_sizer = wx.BoxSizer(wx.HORIZONTAL)
		read_button = wx.Button(self.main_panel, label='Read')
		read_button.Bind(wx.EVT_BUTTON, self.readDeviceKeys)
		controls_sizer.Add(read_button, proportion=1, flag=wx.ALL, border=5)
		clear_button = wx.Button(self.main_panel, label='Clear')
		clear_button.Bind(wx.EVT_BUTTON, self.clearKeys)
		controls_sizer.Add(clear_button, proportion=1, flag=wx.ALL, border=5)
		write_button = wx.Button(self.main_panel, label='Write')
		write_button.Bind(wx.EVT_BUTTON, self.writeKeys)
		controls_sizer.Add(write_button, proportion=1, flag=wx.ALL, border=5)
		main_sizer.Add(controls_sizer, proportion=0, flag=wx.EXPAND)



		self.main_panel.SetSizer(main_sizer)
		# main_sizer.Fit(self.main_panel)

		# create a menu bar
		self.makeMenuBar()

		# and a status bar
		self.SetStatusText("No device connected")
		self.clearKeys(None)


	# def updateKeysPanel(self):
		# wx.StaticText(self.keys_panel, label="switch_count = {}".format(self.switch_count))
		# keys_sizer = wx.BoxSizer(wx.VERTICAL)

		# for index in range(0, self.switch_count):
		# 	self.switch_text_boxes.append(wx.TextCtrl(self.keys_panel))

		# for index, switch_text_box in enumerate(self.switch_text_boxes):
		# 	switch_sizer = wx.BoxSizer(wx.HORIZONTAL)
		# 	switch_sizer.Add(wx.StaticText(self.keys_panel, label="Switch {}".format(index)), proportion=1, flag=wx.CENTER | wx.ALL, border=5)
		# 	switch_sizer.Add(switch_text_box, proportion=6, flag=wx.CENTER | wx.ALL, border=5)
		# 	switch_sizer.Add(wx.Button(self.keys_panel, label="Record"), proportion=1, flag=wx.CENTER | wx.ALL, border=5)
		# 	keys_sizer.Add(switch_sizer, proportion=1, flag=wx.EXPAND)
		# self.keys_panel.SetSizer(keys_sizer)
		# self.keys_panel.Layout()
		# keys_sizer.Fit(self.keys_panel)


	def updateDevices(self, event):
		self.SetStatusText("No device connected")
		SerialDevicesHelper(self).start()


	def selectDevice(self, event):
		try:
			device = self.devices[self.device_select.GetStringSelection()]
			self.current_device = device
			self.SetStatusText("Connecting to {}...".format(device))
			SerialDeviceQueryHelper(self).start()

		except KeyError:
			self.SetStatusText("No device connected")

	def readDeviceKeys(self, event):
		SerialDeviceReadHelper(self).start()

	def clearKeys(self, event):
		self.keys_edit.ClearAll()
		self.keys_edit.MarginSetText(0, "Switch 0")
		self.keys_edit.MarginSetStyle(0, 1)

	def writeKeys(self, event):
		SerialDeviceWriteHelper(self).start()

	
	def updateMargins(self, event):
		lc = self.keys_edit.GetLineCount()
		if lc != self.line_count:
			self.line_count = lc
			for line in range(0, lc):
				self.keys_edit.MarginSetText(line, "Switch {}".format(line))
				self.keys_edit.MarginSetStyle(line, 1)
		# hacky way to shrink the horizontal scrollbar back down when line length decreases
		self.keys_edit.SetScrollWidth(5) 


	def makeMenuBar(self):
		"""
		A menu bar is composed of menus, which are composed of menu items.
		This method builds a set of menus and binds handlers to be called
		when the menu item is selected.
		"""

		# Make a file menu with Hello and Exit items
		# fileMenu = wx.Menu()
		# The "\t..." syntax defines an accelerator key that also triggers
		# the same event
		# helloItem = fileMenu.Append(-1, "&Hello...\tCtrl-H",
				# "Help string shown in status bar for this menu item")
		# fileMenu.AppendSeparator()
		# When using a stock ID we don't need to specify the menu item's
		# label
		# exitItem = fileMenu.Append(wx.ID_EXIT)

		# Now a help menu for the about item
		helpMenu = wx.Menu()
		aboutItem = helpMenu.Append(wx.ID_ABOUT)

		# Make the menu bar and add the two menus to it. The '&' defines
		# that the next letter is the "mnemonic" for the menu item. On the
		# platforms that support it those letters are underlined and can be
		# triggered from the keyboard.
		menuBar = wx.MenuBar()
		# menuBar.Append(fileMenu, "&File")
		menuBar.Append(helpMenu, "&Help")

		# Give the menu bar to the frame
		self.SetMenuBar(menuBar)

		# Finally, associate a handler function with the EVT_MENU event for
		# each of the menu items. That means that when that menu item is
		# activated then the associated handler function will be called.
		# self.Bind(wx.EVT_MENU, self.OnHello, helloItem)
		# self.Bind(wx.EVT_MENU, self.OnExit,  exitItem)
		self.Bind(wx.EVT_MENU, self.OnAbout, aboutItem)


	# def OnExit(self, event):
	# 	"""Close the frame, terminating the application."""
	# 	self.Close(True)


	# # def OnHello(self, event):
	# #     """Say hello to the user."""
	# #     wx.MessageBox("Hello again from wxPython")


	def OnAbout(self, event):
		"""Display an About Dialog"""
		wx.MessageBox("About message here",
					  "ManyKey Writer",
					  wx.OK|wx.ICON_INFORMATION)


if __name__ == '__main__':
	# When this module is run (not imported) then create the app, the
	# frame, show it, and start the event loop.
	app = wx.App()
	frm = GuiFrame(None, title='ManyKey Writer', size=(500,400))
	frm.Show()
	app.MainLoop()
