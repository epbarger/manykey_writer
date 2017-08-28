#!/bin/python
"""
Hello World, but with more meat.
"""

import wx
import serial
import serial.tools.list_ports

class GuiFrame(wx.Frame):
	"""
	A Frame that says Hello World
	"""

	def __init__(self, *args, **kw):
		# ensure the parent's __init__ is called
		super(GuiFrame, self).__init__(*args, **kw)


		self.switch_count = 3
		self.max_keys = 10
		self.switch_text_boxes = []
		self.devices = []
		self.current_device = None


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
		select_device = wx.StaticText(self.main_panel, label="Select Device")
		font = select_device.GetFont()
		font.PointSize -= 0
		font = font.Bold()
		select_device.SetFont(font)
		main_sizer.Add(select_device, proportion=0, flag=wx.ALL, border=5)

		# Device Selection
		device_sizer = wx.BoxSizer(wx.HORIZONTAL)
		self.device_select = wx.Choice(self.main_panel, choices=[])
		device_sizer.Add(self.device_select, proportion=4, flag=wx.ALL, border=5)
		device_refresh_button = wx.Button(self.main_panel, label='Refresh Devices')
		device_sizer.Add(device_refresh_button, proportion=1, flag=wx.ALL, border=5)		
		main_sizer.Add(device_sizer, proportion=0, flag=wx.EXPAND)
		self.refreshDeviceList()

		# Keys Title
		select_keys = wx.StaticText(self.main_panel, label="Set Keys")
		font = select_keys.GetFont()
		font.PointSize -= 0
		font = font.Bold()
		select_keys.SetFont(font)
		main_sizer.Add(select_keys, proportion=0, flag=wx.ALL, border=5)


		# Key Selection Panel
		self.keys_panel = wx.Panel(self.main_panel)
		main_sizer.Add(self.keys_panel, proportion=1, flag=wx.EXPAND)
		self.updateKeysPanel()

		# Controls
		controls_sizer = wx.BoxSizer(wx.HORIZONTAL)
		read_button = wx.Button(self.main_panel, label='Read')
		controls_sizer.Add(read_button, proportion=1, flag=wx.ALL, border=5)
		clear_button = wx.Button(self.main_panel, label='Clear')
		controls_sizer.Add(clear_button, proportion=1, flag=wx.ALL, border=5)
		write_button = wx.Button(self.main_panel, label='Write')
		controls_sizer.Add(write_button, proportion=1, flag=wx.ALL, border=5)
		main_sizer.Add(controls_sizer, proportion=0, flag=wx.EXPAND)



		self.main_panel.SetSizer(main_sizer)
		# main_sizer.Fit(self.main_panel)

		# create a menu bar
		self.makeMenuBar()

		# and a status bar
		self.CreateStatusBar()
		self.SetStatusText("No device connected")

	def updateKeysPanel(self):
		# wx.StaticText(self.keys_panel, label="switch_count = {}".format(self.switch_count))
		keys_sizer = wx.BoxSizer(wx.VERTICAL)

		for index in range(0, self.switch_count):
			self.switch_text_boxes.append(wx.TextCtrl(self.keys_panel))

		for index, switch_text_box in enumerate(self.switch_text_boxes):
			switch_sizer = wx.BoxSizer(wx.HORIZONTAL)
			switch_sizer.Add(wx.StaticText(self.keys_panel, label="Switch {}".format(index)), proportion=1, flag=wx.CENTER | wx.ALL, border=5)
			switch_sizer.Add(switch_text_box, proportion=6, flag=wx.CENTER | wx.ALL, border=5)
			switch_sizer.Add(wx.Button(self.keys_panel, label="Record"), proportion=1, flag=wx.CENTER | wx.ALL, border=5)
			keys_sizer.Add(switch_sizer, proportion=1, flag=wx.EXPAND)
		self.keys_panel.SetSizer(keys_sizer)
		# keys_sizer.Fit(self.keys_panel)

	def refreshDeviceList(self):
		# this.devices = []
		self.device_select.Clear()
		print(self.device_select)
		for port in serial.tools.list_ports.comports():
			# self.devices.append(port)
			print(self.device_select.Append(port))
			print(port)

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
	frm = GuiFrame(None, title='ManyKey Writer', size=(500,500)) #style=wx.MINIMIZE_BOX |  wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX | wx.CLIP_CHILDREN
	frm.Show()
	app.MainLoop()
