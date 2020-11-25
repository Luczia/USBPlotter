# from tkinter import *
# from tkinter import messagebox

# from tkinter import scrolledtext
import tkinter as Tk
#from tkinter.ttk import Frame
from tkinter import Menu, scrolledtext, ttk

import time

from PIL import ImageTk, Image
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

import click
from tkinterify import tkinterify

import pandas as pd

isConnected = False

class Window(Tk.Frame):    

    def new_file(self):
        pass

    def open_file(self):
        pass

    def save_file(self):
        pass
        
    def connection(self):
        global isConnected
        if isConnected :
            connectedLED.create_oval(3, 2, 26, 26, width=0, fill='red')
            connectedLED.pack(padx=2, pady=4)
            isConnected = False
        else :
            connectedLED.create_oval(3, 2, 26, 26, width=0, fill='green')
            connectedLED.pack(padx=2, pady=4)
            isConnected = True

    def quit_software(self):
        self.master.destroy()
        
    def select(self):
        pass

    def a_propos(self):
        mon_message = messagebox.showinfo("This app plots real time data for debugging:", "AURA Project \n http://oxio-dynamics.com/en/ \n Lucas Soubeyrand")

    def graph(self):
        angle = np.random.normal(180,180,1000)
        plt.hist(angle, 50)
        plt.show()

    def listSelect(self, val):
        sender = val.widget
        idx = sender.curselection()    
        selected_text_list = [sender.get(i) for i in sender.curselection()]    
        value =""
        for j in idx:        
            value += sender.get(j)
            value+=" - "    
        var.set(value)

        cli.config(state='normal')
        cli.delete(1.0, END)
        cli.insert(END, value)
        cli.config(state='disabled')

        pass

    def __init__(self, figure, master, SerialReference):
        Tk.Frame.__init__(self, master)
        self.entry = None
        self.setPoint = None
        self.master = master        # a reference to the master window
        self.serialReference = SerialReference      # keep a reference to our serial connection so that we can use it for bi-directional communicate from this class
        self.initWindow(figure)     # initialize the window with our settings

    def initWindow(self, figure):
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
        eimg_plug = ImageTk.PhotoImage(img_plug)
        eimg_exit = ImageTk.PhotoImage(img_exit)

        connectedLED = Tk.Canvas(toolbar, width=32, height=32)
        connectedLED.create_oval(3, 2, 26, 26, width=0, fill='red')
        connectedLED.pack(padx=2, pady=4)

        connectButton = Tk.Button(toolbar, height=20, width=20, relief=Tk.FLAT, command=self.connection)
        connectButton.image = eimg_plug
        connectButton.pack(side=Tk.TOP, padx=2, pady=4)

        exitButton = Tk.Button(toolbar, height=20, width=20, relief=Tk.FLAT, command=self.quit_software)
        exitButton.image = eimg_exit
        exitButton.pack(side=Tk.TOP, padx=2, pady=4)
 
        toolbar.pack(side=Tk.RIGHT, fill=Tk.X)

        # lowbar
        lowbar = Tk.Frame(self.master, bg='white', height=150, relief='sunken', borderwidth=2)
        lowbar.pack(expand=True, fill='both', side='bottom', anchor='nw')

        cli = scrolledtext.ScrolledText(lowbar, height=10, bg='black', fg='white')
        #cli.insert(INSERT,'You text goes here')
        cli.pack()

        # sidebar
        sidebar = Tk.Frame(self.master, width=200, bg='white', height=500, relief='sunken', borderwidth=2)
        sidebar.pack(expand=False, fill='both', side='left', anchor='nw')
        lbl2 = Tk.Label(sidebar, text= 'Choose data to be sent')
        lbl2.pack()

        # main content area
        mainarea = Tk.Frame(self.master, bg='#CCC', width=500, height=500)
        mainarea.pack(expand=True, fill='both', side='right')


        tab_control = ttk.Notebook(mainarea)
        tab_live = ttk.Frame(tab_control)
        tab_offline = ttk.Frame(tab_control)

        tab_control.add(tab_live, text='LivePlot')
        tab_control.add(tab_offline, text='Desynchronous Plot')
        lbl1 = Tk.Label(tab_live, text= 'label1')
        lbl1.pack()
        # lbl1.grid(column=0, row=0)
        lbl2 = Tk.Label(tab_offline, text= 'label2')
        # lbl2.grid(column=0, row=0)

        # cb = Checkbutton(sidebar, bg='white', text="VoltU", command=CheckbuttonClick )
        # cb.pack(side='bottom')
        # cb.select()
        # cb.place(x=5, y=25)

        physical_quantity = ['VoltU', 'VoltV', 'VoltW',
                    'CurU', 'CurV', 'CurW',
                        'Enc', 'Mot', 'SofMot']

        lb = Tk.Listbox(sidebar, selectmode=Tk.EXTENDED)

        for i in physical_quantity:
            lb.insert(Tk.END, i)

        lb.bind("<<ListboxSelect>>", self.listSelect)

        lb.pack(pady=15)

        var = Tk.StringVar()
        label = Tk.Label(sidebar, text=0, textvariable=var)
        label.pack()

        canvas = FigureCanvasTkAgg(figure, master=tab_live)
        toolbar = NavigationToolbar2Tk(canvas, tab_live)
        canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)

        tab_control.pack(expand=1, fill='both')


class serialPlot:
    def __init__(self, serialPort='/dev/ttyUSB0', serialBaud=38400, plotLength=100, dataNumBytes=2, numPlots=1):
        self.port = serialPort
        self.baud = serialBaud
        self.plotMaxLength = plotLength
        self.dataNumBytes = dataNumBytes
        self.numPlots = numPlots
        self.rawData = bytearray(numPlots * dataNumBytes)
        self.dataType = None
    
    def getSerialData(self, frame, lines, lineValueText, lineLabel, timeText):
        currentTimer = time.process_time()
        self.plotTimer = int((currentTimer - self.previousTimer) * 1000)     # the first reading will be erroneous
        self.previousTimer = currentTimer
                # timeText.set_text('Plot Interval = ' + str(self.plotTimer) + 'ms')
    

def main():
    # portName = 'COM5'
    portName = '/dev/ttyUSB0'
    baudRate = 38400
    maxPlotLength = 100     # number of points in x-axis of real time plot
    dataNumBytes = 4        # number of bytes of 1 data point
    numPlots = 3            # number of plots in 1 graph
    s = serialPlot(portName, baudRate, maxPlotLength, dataNumBytes, numPlots)   # initializes all required variables
    # s.readSerialStart()                                               # starts background thread

    # plotting starts below
    pltInterval = 50    # Period at which the plot animation updates [ms]
    xmin = 0
    xmax = maxPlotLength
    ymin = -(1)
    ymax = 1
    fig = plt.figure(figsize=(10, 8))
    ax = plt.axes(xlim=(xmin, xmax), ylim=(float(ymin - (ymax - ymin) / 10), float(ymax + (ymax - ymin) / 10)))
    ax.set_title('Arduino Accelerometer')
    ax.set_xlabel("Time")
    ax.set_ylabel("Accelerometer Output")

    # put our plot onto Tkinter's GUI
    root = Tk.Tk()    
    app = Window(fig, root, s)




    lineLabel = ['X', 'Y', 'Z']
    style = ['r-', 'c-', 'b-']  # linestyles for the different plots
    timeText = ax.text(0.70, 0.95, '', transform=ax.transAxes)
    lines = []
    lineValueText = []
    for i in range(numPlots):
        lines.append(ax.plot([], [], style[i], label=lineLabel[i])[0])
        lineValueText.append(ax.text(0.70, 0.90-i*0.05, '', transform=ax.transAxes))
    anim = animation.FuncAnimation(fig, s.getSerialData, fargs=(lines, lineValueText, lineLabel, timeText), interval=pltInterval)    # fargs has to be a tuple

    plt.legend(loc="upper left")
    root.mainloop()   # use this instead of plt.show() since we are encapsulating everything in Tkinter

    s.close()


if __name__ == '__main__':
    main()




# container = tk.Frame(self)
# container.pack(side="top", fill="both", expand = True)
# container.grid_rowconfigure(0,weight=1)
# container.grid_columncoinfigure(0, weight=1)

# lg=300
# ht=200
# bw=50
# zf=10
# dessin=Canvas(tab_live, bg="ivory", width=lg,height=ht, bd=bw,  highlightthickness=zf, highlightbackground="sky blue")
# dessin.pack(side='left', padx=20, pady=20)

# my_button = Button(sidebar, text ="Send", command=graph)
# my_button.pack()

# window.mainloop()


