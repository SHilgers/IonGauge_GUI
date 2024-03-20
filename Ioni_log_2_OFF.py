#Program to record and save the pressure with a graphical interface that displays 
#and plots the pressure.Old data can be read in and plotted as well. 
#Connection to Ioni via Moxa port/ socket. Serial communication is also possible, 
#not implemented here.

import csv
from socket import * #For communication with moxa a socket is used
import time
import sys
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtCore import QTimer,QDateTime
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import matplotlib
import datetime
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib.dates as mdates
from matplotlib.dates import DateFormatter
import os.path   #for checking if file exists
from os import path

filename=False
time_list=[0]*1200 #list of 1200 Zeros, data of 20 minutes
pressure_list=[0]*1200

#commonication with moxa
serverHost='129.217.168.64'
serverPort= 4003
s=socket(AF_INET, SOCK_STREAM) #create a TCP socket
s.connect((serverHost, serverPort)) #connect to server on the port


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QGridLayout(self)
        self.setWindowTitle("Ioni GUI")
        self.left = 100
        self.top = 10
        self.width =1000
        self.height = 3000
        self.sub_window = None


        self.label = QLabel("pressure/mbar",self)
        #self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("QLabel { font-size: 25pt; font-weight: 600}")
        #self.label.setStyleSheet(f'font-weight: {600}')


        self.output= QLabel(self)
        #self.output.setFixedWidth()       
        self.output.setStyleSheet("QLabel { background-color : lightgrey; color : red; font-weight: 700; font-size: 70pt}")
        self.output.setAlignment(Qt.AlignCenter)

        self.button_plotday=QPushButton('Plot Day', self)
        self.label_plotday=QLabel('Plot day: YYYY-MM-DD')
        self.input_plotday=QLineEdit(self)    
    

        vbox_label=QVBoxLayout()
        vbox_label.addWidget(self.label)
        self.layout.addLayout(vbox_label, 0, 0, 1, 1)

        vbox_output=QVBoxLayout()
        vbox_output.addWidget(self.output)
        self.layout.addLayout(vbox_output, 1, 0, 2, 1)

        vbox_plotday=QVBoxLayout()
        vbox_plotday.addWidget(self.label_plotday)
        vbox_plotday.addWidget(self.input_plotday)
        vbox_plotday.addWidget(self.button_plotday)
        self.layout.addLayout(vbox_plotday, 12, 0, 3, 2)


        self.figure1 = plt.figure() # a figure instance to plot on
                                        
        self.canvas1 = FigureCanvas(self.figure1) # this is the Canvas Widget that
                                                # displays the 'figure'it takes the
                                                # 'figure' instance as a parameter to __init__ 
        
        self.toolbar1 = NavigationToolbar(self.canvas1, self)  # this is the Navigation widget
                                                            # it takes the Canvas widget an

        vbox_plot= QVBoxLayout()          #Layout für Plot
        vbox_plot.addWidget(self.toolbar1)
        vbox_plot.addWidget(self.canvas1)
        self.layout.addLayout(vbox_plot, 4, 0, 8, 1)    

        plt.cla() #clean plot
        self.canvas1.draw() #update plot
        self.Run()
        # Button Event
        self.button_plotday.clicked.connect(self.clicked) 
       
        
    def clicked(self): 
        #self.read_fname()        
        if self.read_fname():                                    # self.read_fname is called. Subwindow is only opened if the return is True,
            self.sub_window = SubWindow(fname=self.fname_main)   # which means if the path exists. If the path doesn't exist, else-case, so print to the terminal.
            self.sub_window.show() # Sub Window
        else:
            print('File does not exists!')

    def read_fname(self):
        self.fname_main=str(self.input_plotday.displayText()) #read text from input
        print(self.fname_main)
        check_exists=path.exists('Ioni-data/'+ self.fname_main +'.csv')   #check if path exists
        return check_exists
        

    def Run(self):
        self.timer=QTimer()
        self.timer.start(1000)
        self.timer.timeout.connect(self.ReadPressure)

        self.timer_plot=QTimer()  #QTimer needs to be restarted here, otherwise it won't work properly on the second call (adds as many seconds as clicks)
        self.timer_plot.start(1000)
        self.timer_plot.timeout.connect(self.plot) # The timeout command calls the given function (here: plot) every second (starting at 1000ms) and thus updates
                                                   # until the timer is stopped

        #self.button_plotday.clicked.connect(self.plotday) 
        return


    def ReadPressure(self):
        global current_time, time_list, pressure_list
       
        s.send('*S0'.encode())  #*S0 fragt Status ab
        pressure_string_all=s.recv(128)  #string
        pressure_string=pressure_string_all[9:16]   #take only interesting value
        if(not (pressure_string and not pressure_string.isspace())):
        	pressure=0
        else:
        	pressure = float(pressure_string.decode()) #change to float
        
        self.output.setText(str(pressure))

        self.CheckDay()                    
        with open ('Ioni-data/'+filename + ".csv", "a") as f: #Create a new file if it does not exist:
            writer= csv.writer(f, delimiter=",")
            writer.writerow([time.strftime("%H:%M:%S", time.localtime()),pressure])

        time_list.pop(0) #remove first element of list
        time_list.append(time.strftime("%H:%M:%S", time.localtime()))
        pressure_list.pop(0)
        pressure_list.append(pressure)
        return pressure    
      
    
    def CheckDay(self):   #Check Date. If it has changed create a new file named by the day
        global filename
        RunDay=datetime.today().strftime('%Y-%m-%d')
        #print(RunDay)
        if filename == RunDay:
            return filename

        else:
            filename=RunDay
            return filename


    def plot(self):
        #plt.ion()  #interactive mode 
        self.figure1.clf()
        ax=self.figure1.add_subplot()
        ax.plot(time_list,pressure_list)
        ax.set_xlabel("time")
        ax.set_ylabel("pressure in mbar")
        ax.set_yscale('log')
        ax.xaxis.set_major_locator(plt.MaxNLocator(7))
        self.canvas1.draw_idle()
        plt.tight_layout()
        # self.canvas.draw()

    #ask before close
    def closeEvent(self, event):
	    reply = QMessageBox.question(self, 'Window Close', 'Are you sure you want to close the window?',
				QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

	    if reply == QMessageBox.Yes:
		    event.accept()
		    print('Window closed')
	    else:
		    event.ignore()

    
class SubWindow(QWidget):
     def __init__(self, fname):   #fname input from Mainwindow
        super(SubWindow,self).__init__()
        self.layout = QGridLayout(self)
        self.resize(800, 500)
        self.setWindowTitle("Day")
           
     
        self.figure2 = plt.figure() # a figure instance to plot on         
        self.canvas2 = FigureCanvas(self.figure2) # this is the Canvas Widget that
                                                # displays the 'figure'it takes the
                                                # 'figure' instance as a parameter to __init__        
        self.toolbar2 = NavigationToolbar(self.canvas2, self)  # this is the Navigation widget
                                                            # it takes the Canvas widget an
 
       
        vbox_plot= QVBoxLayout()          #Layout for plots
        vbox_plot.addWidget(self.toolbar2)
        vbox_plot.addWidget(self.canvas2)
        self.layout.addLayout(vbox_plot, 0, 0, 3, 3)    

        #read Data from main window
        self.fname = fname
        #print(self.fname)     
        
        data = pd.read_csv('Ioni-data/'+ self.fname +'.csv', sep=',',header=None)
        time_str = data[0]
        time = [datetime.strptime(x, '%H:%M:%S') for x in time_str] #Reformatting the data from string to something else
        pressure = data[1]

        ax=self.figure2.add_subplot()
        ax.clear()
        ax.plot(time, pressure)
        date_form = mdates.DateFormatter("%H:%M")
        ax.xaxis.set_major_formatter(date_form)
        ax.set_xlabel("time")
        ax.set_ylabel("pressure in mbar")
        ax.set_title(self.fname)
        ax.set_yscale('log')
        #plt.grid(which='major', axis='both')
        #plt.ion()            
          
        self.canvas2.draw() #update plot
        #self.canvas2.flush_events() # flush the GUI events
        plt.close()

   
        
app = QApplication(sys.argv)
window = App()
window.show()

app.exec()



