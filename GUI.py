# from tkinter import *
# from tkinter import messagebox
 
try:
	# python 2.x
	import Tkinter as Tk
	from Tkinter import scrolledtext, ttk
except ImportError:
	# python 3.x
	import tkinter as Tk
	from tkinter import scrolledtext, ttk

import time
import serial
import collections
import struct
import copy

from PIL import ImageTk, Image
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.widgets import Slider

import pandas as pd
from threading import Thread

isConnected = False


class Window(Tk.Frame):	   
	
	physical_quantity = ['VoltU', 'VoltV', 'VoltW',	 'CurU', 'CurV', 'CurW',  'HardEnc', 'Mot', 'SofEnc'] 
	selected_data = []
	
	lines = []
	lineValueText = []
	lineLabel = []
	  
	x=[]
	y1=[]
	y2=[]
	y3=[]
	y4=[]
	y5=[]
	
	xmin = xmax = ymin = ymax = 0

	 
	def __init__(self, figure, master, SerialReference, pltInterval):
		Tk.Frame.__init__(self, master)
		self.entry = None
		self.setPoint = None
		self.master = master		# a reference to the master window
		self.serialReference = SerialReference		# keep a reference to our serial connection so that we can use it for bi-directional communicate from this class
		self.figure = figure
		self.pltInterval = pltInterval
		self.initWindow(figure, SerialReference)	 # initialize the window with our settings
		self.previousTimer = 0
		self.xmin = 0
		self.xmax = 20
		self.ymin = -2
		self.ymax = 6
		self.dataNumBytes = 2
		if self.dataNumBytes == 2:
			self.dataType = 'e'		# 2 byte integer h  | https://docs.python.org/3/library/struct.html 
		elif self.dataNumBytes == 4:
			self.dataType = 'f'		# 4 byte float	 f
		self.plotMaxLength = 100 #Number of data plotted in the x axis
		self.numPlots = 10	#TODO : Link with get_list number or use as SUPERRGLOBAL   #len(self.physical_quantity)
		self.data = []
		self.rawData = []
		for i in range(self.numPlots):   # give an array for each type of data and store them in a list
			self.data.append(collections.deque([0] * self.plotMaxLength, maxlen=self.plotMaxLength))
		

	def initWindow(self, figure, SerialReference):
		self.master.title("MCARA Real Time Plot")
		self.master.geometry("1080x720")
		self.master.iconbitmap('Logo Small.ico')	   
						
		#barremenu
		barremenu = Tk.Menu(self.master)
		self.master.config(menu = barremenu)

		fichier_menu = Tk.Menu(barremenu, tearoff = 0)
		barremenu.add_cascade(label = "File", menu = fichier_menu)
		fichier_menu.add_command(label = "New", command = self.new_file)
		fichier_menu.add_command(label = "Open", command = self.open_file)
		fichier_menu.add_command(label = "Save", command = self.save_file)
		fichier_menu.add_separator()
		fichier_menu.add_command(label = "Quit software", command = self.quit_software)

		edition_menu = Tk.Menu(barremenu, tearoff = 0)
		barremenu.add_cascade(label = "Edit", menu = edition_menu)
		edition_menu.add_command(label = "Select", command = self.select)

		apropos = Tk.Menu(barremenu, tearoff = 0)
		barremenu.add_cascade(label = "A propos", menu = apropos)
		apropos.add_command(label = "Infos", command = self.a_propos)

		
		#toolbar
		toolbar = Tk.Frame(self.master, bd=1, relief=Tk.SUNKEN)

		img_plug = Image.open("plug.png")
		img_exit = Image.open("exit.png")
		eimg_plug = ImageTk.PhotoImage(img_plug, master=self.master)
		eimg_exit = ImageTk.PhotoImage(img_exit, master=self.master)

		self.connectedLED = Tk.Canvas(toolbar, width=32, height=32)
		self.connectedLED.create_oval(3, 2, 26, 26, width=0, fill='red')
		self.connectedLED.pack(padx=2, pady=4)

		connectButton = Tk.Button(toolbar, image=eimg_plug, height=20, width=20, relief=Tk.FLAT, command=self.connection)
		connectButton.image = eimg_plug
		connectButton.pack(side=Tk.TOP, padx=2, pady=4)

		exitButton = Tk.Button(toolbar, image=eimg_exit, height=20, width=20, relief=Tk.FLAT, command=self.quit_software)
		exitButton.image = eimg_exit
		exitButton.pack(side=Tk.TOP, padx=2, pady=4)
 
		toolbar.pack(side=Tk.RIGHT, fill=Tk.X)

		# lowbar
		lowbar = Tk.Frame(self.master, bg='white', height=150, relief='sunken', borderwidth=2)
		lowbar.pack(expand=True, fill='both', side='bottom', anchor='nw')

		self.cli = Tk.scrolledtext.ScrolledText(lowbar, height=10, bg='black', fg='white')
		self.cli.pack(expand=True, fill='both')

		# sidebar
		sidebar = Tk.Frame(self.master, width=200, bg='white', height=500, relief='sunken', borderwidth=2)
		sidebar.pack(expand=True, fill='both', side='left', anchor='nw')
		lbl2 = Tk.Label(sidebar, text= 'Choose data to be sent')
		lbl2.pack()

		# main content area with tabs
		mainarea = Tk.Frame(self.master, bg='#CCC', width=500, height=500)
		mainarea.pack(expand=True, fill='both', side='right')

		tab_control = ttk.Notebook(mainarea)
		tab_live = ttk.Frame(tab_control)
		tab_offline = ttk.Frame(tab_control)

		tab_control.add(tab_live, text='LivePlot')
		tab_control.add(tab_offline, text='Desynchronous Plot')
		lbl1 = Tk.Label(tab_live, text= 'label1')		 
		lbl2 = Tk.Label(tab_offline, text= 'label2')
		lbl1.pack()		  
				  

		lb = Tk.Listbox(sidebar, selectmode=Tk.EXTENDED)
		for i in self.physical_quantity:
			lb.insert(Tk.END, i)
		lb.bind("<<ListboxSelect>>", self.listSelect)
		lb.pack(pady=15)

		self.var = Tk.StringVar()
		label = Tk.Label(sidebar, text=0, textvariable=self.var)
		label.pack()
		
		plt.style.use('ggplot') #More sophisticated background
		self.ax = plt.axes()
		self.spos = Slider(self.ax, 'Pos', 2, 90.0)
		self.updatePlotLabels()
		self.spos.on_changed(self.sliderUpdate)
		canvas = FigureCanvasTkAgg(figure, master=tab_live)
		canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)

		tab_control.pack(expand=1, fill='both')
	   

	def new_file(self):
		pass

	def open_file(self):
		pass

	def save_file(self):
		pass
		
	def connection(self):
		global isConnected
		if isConnected :
			self.connectedLED.create_oval(3, 2, 26, 26, width=0, fill='red')
			self.connectedLED.pack(padx=2, pady=4)
			isConnected = False
			self.serialReference.disconnectSerialBus()
			self.updateCLI("Disconection\n")
		else :
			self.connectedLED.create_oval(3, 2, 26, 26, width=0, fill='green')
			self.connectedLED.pack(padx=2, pady=4)
			isConnected = True
			self.serialReference.connectSerialBus()
			self.updateCLI("Conection\n")

	def quit_software(self):
		self.master.destroy()
		
	def select(self):
		pass

	def a_propos(self):
		mon_message = Tk.messagebox.showinfo("This app plots real time data for debugging:", "AURA Project \n http://oxio-dynamics.com/en/ \n Lucas Soubeyrand")

	def graph(self):
		angle = np.random.normal(180,180,1000)
		plt.hist(angle, 50)
		plt.show()

	def sliderUpdate(self, val):
		pos = spos.val
		self.x.axis([pos,pos+10,-1,1])

	def listSelect(self, val):
		sender = val.widget
		idx = sender.curselection()	   
		selected_text_list = [sender.get(i) for i in sender.curselection()]	   
		self.selected_data = selected_text_list
		value =""
		for j in idx:		 
			value += sender.get(j)
			value+=" - "	
		self.var.set(value)

		string = "New variable selected: "+value+"\n"
		self.updateCLI(string)
		self.updatePlotLabels()
		
		pass

	def updateCLI(self,str):
		self.cli.config(state='normal')
		# cli.delete(1.0, END)
		self.cli.insert(Tk.END, str)
		self.cli.config(state='disabled')
		self.cli.see("end")
	
	def updatePlotLabels(self):

		try :
			self.anim.event_source.stop()			 
		except :
			print("First Launch - Can't Stop anim")
		
		self.lineLabel = self.selected_data 
		style = ['lightcoral', 'black', 'chocolate', 'palegreen', 'gold', 'darkorange', 'forestgreen', 'deepskyblue', 'slategray', 'navy', 'indigo', 'mangenta' ,'lightpink' ]	# linestyles for the different plots
		
		self.ax.clear()
		self.ax.set_xlim([self.xmin,self.xmax])
		self.ax.set_ylim([self.ymin,self.ymax])
		# self.ax.set_autoscalex_on(True)
		self.ax.set_xlabel("Time")
		self.ax.set_ylabel("STM32 Output")
		self.line, = self.ax.plot([], [], linewidth=2)

		for self.line in self.lines:
			self.line.remove()
			del self.line			 
		self.lines[:] = []
		
		for i in range(len(self.selected_data)):
			self.lines.append(self.ax.plot([], [], style[i],label=self.lineLabel[i])[0])
			# self.lineValueText.append(self.ax.text(0.70, 0.90-i*0.05, '', transform=self.ax.transAxes))

		print(self.selected_data)
		self.timeText = self.ax.text(0.70, 0.95, '', transform=self.ax.transAxes)
		self.timeText.set_text('Plot Interval = ' + 'X' + 'ms')		   
		self.ax.legend(frameon=False, loc='upper center', ncol=2) 

		
		# self.anim = animation.FuncAnimation(fig=self.figure, func=self.animate, frames=self.serialReference.genData,  init_func=self.init_anim, interval=self.pltInterval, blit=False,  fargs=(serialRef))   
		self.anim = animation.FuncAnimation(fig=self.figure, func=self.animate, fargs=(self.serialReference.rawData, 4), init_func=self.init_anim, interval=self.pltInterval, blit=False,  )   

	def init_anim(self):   
		for self.line in self.lines:
			self.line.set_data([], [])	  
		return self.lines  

	
	def animate(self, frame, serialRefData, numPlots):
				
		currentTimer = time.process_time()
		plotTimer = int((currentTimer - self.previousTimer) * 1000)		# the first reading will be erroneous
		self.previousTimer = currentTimer
		self.timeText.set_text('Plot Interval = ' + str(plotTimer) + 'ms')
		
		privateData = copy.deepcopy(serialRefData)
		# privateData = copy.deepcopy(frame)
		for i in range(self.numPlots):
			data = privateData[(i*self.dataNumBytes):(self.dataNumBytes + i*self.dataNumBytes)]
			value,  = struct.unpack(self.dataType, data)
			if value > 0.01 or value < -0.01 :
				self.data[i].append(value)    # we get the latest data point and append it to our array
				print(value)
		
		for i in range(len(self.lines)):
			self.lines[i].set_data(range(self.plotMaxLength), self.data[i])
		
		if(currentTimer > self.xmax):
			self.ax.set_xlim([currentTimer-self.xmax,currentTimer])
			  

class serialExtract:

	physical_quantity = ['VoltU', 'VoltV', 'VoltW',	 'CurU', 'CurV', 'CurW',  'HardEnc', 'Mot', 'SofEnc']
	physical_quantity.append('Time')
	data_amount = 2 

	def __init__(self, serialPort='/dev/ttyUSB0', serialBaud=115200, dataNumBytes=2):
		
		self.port = serialPort
		self.baud = serialBaud		
		self.dataNumBytes = dataNumBytes		
		self.rawData = bytearray(len(self.physical_quantity) * dataNumBytes)
				
		self.isRun = True
		self.isReceiving = False
		self.thread = None

	  
	def connectSerialBus(self):		
		print('Trying to connect to: ' + str(self.port) + ' at ' + str(self.baud) + ' BAUD.')
		try:
			self.serialConnection = serial.Serial(self.port, self.baud, timeout=4)
			print('Connected to ' + str(self.port) + ' at ' + str(self.baud) + ' BAUD.')
			self.isRun = True
		except:
			print("Failed to connect with " + str(self.port) + ' at ' + str(self.baud) + ' BAUD.')
		#start thread
		if self.thread == None and self.isRun == True:
			self.thread = Thread(target=self.backgroundThread)
			self.thread.start()
			# Block till we start receiving values
			while self.isReceiving != True:
				time.sleep(0.1)

	def genData(self):		  
		i = time.process_time()

		y1 = (np.sin(2 * np.pi * (i)))
		y2 = (np.sin(2 * np.pi * (2*i)+0.25))
		y3 = (np.sin(2 * np.pi * (3*i))-0.25)
		y4 = (np.sin(2 * np.pi * (4*i)-0.5))
		y5 = (np.sin(3 * np.pi * (2*i+0 - 0.01 * i*2)))
		y6 = (np.sin(3 * np.pi * (3*i+0 - 0.01 * i*2)))
		y7 = (np.sin(3 * np.pi * (i+1 - 0.01 * i*2)))
		y8 = (np.sin(3 * np.pi * (i+0 - 0.4 * i*3))-0.1)
		y9 = (np.sin(3 * np.pi * (i+2 - 0.01 * i*2))+1)

		cur_data = struct.pack('10e', y1,y2,y3,y4,y5,y6,y7,y8,y9,i) #'10e' cause we plot 10 float on 2 bytes => https://docs.python.org/3/library/struct.html 
		print("GenData")
		print(i)		
		return cur_data  #yield means we provide an iterable accesible only once
				
	
	def backgroundThread(self):	   # retrieve data
		time.sleep(1.0)  # give some buffer time for retrieving data
        # self.serialConnection.reset_input_buffer()
		while(self.isRun):
			# self.serialConnection.readinto(self.rawData)
			time.sleep(0.1)
			self.rawData = self.genData()
			# print(self.rawData)
			self.isReceiving = True
			#print(self.rawData)
	
	def disconnectSerialBus(self):
		self.isRun = False		 
		self.thread.join() 
		try :
			self.serialConnection.close()
			print('Disconnected...')
		except :
			print("No Connection to close")
		# df = pd.DataFrame(self.csvData)
		# df.to_csv('/home/rikisenia/Desktop/data.csv')

def main():
	# portName = 'COM5'
	portName = '/dev/ttyUSB0'
	baudRate = 115200	
	dataNumBytes = 4		# number of bytes of 1 data point
	s = serialExtract(portName, baudRate, dataNumBytes)	  # initializes all required variables
	# s.readSerialStart()												# starts background thread
	maxPlotLength = 100		# number of points in x-axis of real time plot
	pltInterval = 100	# Period at which the plot animation updates [ms]
	
	fig = plt.figure(figsize=(10, 8))
  
	# put our plot onto Tkinter's GUI
	root = Tk.Tk()	  
	app = Window(fig, root, s, pltInterval)
	
	root.mainloop()	  # use this instead of plt.show() since we are encapsulating everything in Tkinter

	s.disconnectSerialBus()




if __name__ == '__main__':
	main()
