import Tkinter

class IPApp(Tkinter.Tk):
    def __init__(self,parent, hostIP, ipadIP, *args):
        Tkinter.Tk.__init__(self,parent)
        self.parent = parent
        self.hostIP = hostIP
        self.ipadIP = ipadIP
        if(len(args) > 0):
            self.multbool = True
            self.multiloop = args[0]
        self.initialize()

    def initialize(self):
        self.grid()

        self.labelVariable2 = Tkinter.StringVar()
        labelTop = Tkinter.Label(self,textvariable=self.labelVariable2,
                              anchor="w",fg="white",bg="blue")
        labelTop.grid(column=0,row=0,columnspan=2,sticky='EW')
        self.labelVariable2.set(u"Your computer's IP address is: " + self.hostIP +
            "\nEnter this into your iPad\n\nEnter your iPad's IP address below:")

        self.entryVariable = Tkinter.StringVar()
        self.entry = Tkinter.Entry(self,textvariable=self.entryVariable)
        self.entry.grid(column=0,row=1,sticky='EW')
        self.entry.bind("<Return>", self.OnPressEnter)
        self.entryVariable.set(u""+self.ipadIP)

        button = Tkinter.Button(self,text=u"Enter",
                                command=self.OnButtonClick)
        button.grid(column=1,row=1)

        self.labelVariable = Tkinter.StringVar()
        label = Tkinter.Label(self,textvariable=self.labelVariable,
                              anchor="w",fg="white",bg="blue")
        label.grid(column=0,row=2,columnspan=2,sticky='EW')
        self.labelVariable.set(u"Hello !")

        self.grid_columnconfigure(0,weight=1)
        self.resizable(True,False)
        self.update()
        self.geometry(self.geometry())       
        self.entry.focus_set()
        self.entry.selection_range(0, Tkinter.END)

    def OnButtonClick(self):
        self.ipadIP = self.entryVariable.get()
        self.labelVariable.set( self.entryVariable.get() )
        self.entry.focus_set()
        self.entry.selection_range(0, Tkinter.END)
        if self.multbool: self.multiloop.iPadIP = self.ipadIP
        self.destroy()

    def OnPressEnter(self,event):
        self.ipadIP = self.entryVariable.get()
        self.labelVariable.set( self.entryVariable.get() )
        self.entry.focus_set()
        self.entry.selection_range(0, Tkinter.END)
        if self.multbool: self.multiloop.iPadIP = self.ipadIP
        self.destroy()

class ModeSelect(Tkinter.Tk):
    def __init__(self,parent, resultlist):
        Tkinter.Tk.__init__(self,parent)
        self.parent = parent
        self.resultlist = resultlist
        self.initialize()

    def initialize(self):
        self.grid()

        button1 = Tkinter.Button(self,text=u"Solo Mode",
                                command=self.OnButtonClick1)
        button1.grid(column=0,row=0)

        button2 = Tkinter.Button(self,text=u"Network Master",
                                command=self.OnButtonClick2)
        button2.grid(column=1,row=0)

        button3 = Tkinter.Button(self,text=u"Network Slave",
                                command=self.OnButtonClick3)
        button3.grid(column=2,row=0)


    def OnButtonClick1(self):
        self.resultlist.append(0)
        self.destroy()

    def OnButtonClick2(self):
        self.resultlist.append(1)
        self.destroy()

    def OnButtonClick3(self):
        self.resultlist.append(2)
        self.destroy()

class SendNameGUI(Tkinter.Tk):
    def __init__(self,parent, *args):
        Tkinter.Tk.__init__(self,parent)
        self.parent = parent
        if(len(args) > 0):
            self.multbool = True
            self.multiloop = args[0]
        else:
            self.multbool = False
        self.initialize()

    def initialize(self):
        self.grid()

        self.labelVariable2 = Tkinter.StringVar()
        labelTop = Tkinter.Label(self,textvariable=self.labelVariable2,
                              anchor="w",fg="white",bg="blue")
        labelTop.grid(column=0,row=0,columnspan=2,sticky='EW')
        self.labelVariable2.set(u"Who do you want to send to:")

        self.entryVariable = Tkinter.StringVar()
        self.entry = Tkinter.Entry(self,textvariable=self.entryVariable)
        self.entry.grid(column=0,row=1,sticky='EW')
        self.entry.bind("<Return>", self.OnPressEnter)
        self.entryVariable.set(u"all")

        button = Tkinter.Button(self,text=u"Enter",
                                command=self.OnButtonClick)
        button.grid(column=1,row=1)

        self.labelVariable = Tkinter.StringVar()
        label = Tkinter.Label(self,textvariable=self.labelVariable,
                              anchor="w",fg="white",bg="blue")
        label.grid(column=0,row=2,columnspan=2,sticky='EW')
        self.labelVariable.set(u"Hello!")

        self.grid_columnconfigure(0,weight=1)
        self.resizable(True,False)
        self.update()
        self.geometry(self.geometry())       
        self.entry.focus_set()
        self.entry.selection_range(0, Tkinter.END)

    def OnButtonClick(self):
        self.labelVariable.set( self.entryVariable.get() )
        self.entry.focus_set()
        self.entry.selection_range(0, Tkinter.END)
        if self.multbool: self.multiloop.destname = self.entryVariable.get()
        self.destroy()

    def OnPressEnter(self,event):
        self.labelVariable.set( self.entryVariable.get() )
        self.entry.focus_set()
        self.entry.selection_range(0, Tkinter.END)
        if self.multbool: self.multiloop.destname = self.entryVariable.get()
        self.destroy()

if __name__ == "__main__":
    app = SendNameGUI(None)
    app.title('my application')
    app.mainloop()

    print "yo digity"