import socket
from tkinter import *
from tkinter import messagebox
import copy
import time
import re

class Login(Frame):

    def __init__(self):
        Frame.__init__(self)
        self.pack()
        self.master.title("Login")
        self.master.geometry("250x150")

        self.frame1 = Frame(self)
        self.frame1.pack(padx=5, pady=5)

        self.userNameLbl = Label(self.frame1, text="User name")
        self.userNameLbl.pack(side=LEFT, padx=5, pady=5)

        self.userNameEntry = Entry(self.frame1, name="username")
        self.userNameEntry.pack(padx=5, pady=5)

        self.frame2 = Frame(self)
        self.frame2.pack(padx=5, pady=5)

        self.passwordLbl = Label(self.frame2, text="Password")
        self.passwordLbl.pack(side=LEFT, padx=5, pady=5)

        self.passwordEntry = Entry(self.frame2, name="password", show="*")
        self.passwordEntry.pack(padx=5, pady=5)

        self.frame3 = Frame(self)
        self.frame3.pack(padx=5, pady=5)

        self.loginBtn = Button(self.frame3, text="Login", command=self.buttonPressed)
        self.loginBtn.pack(padx=5, pady=5)

    def buttonPressed(self):
        userName = self.userNameEntry.get()
        password = self.passwordEntry.get()
        clientMsg = "login;" + userName + ";" + password
        msg = ("CLIENT>>> " + clientMsg).encode()
        clientSocket.send(msg)
        serverMsg = clientSocket.recv(1024).decode()
        print(serverMsg)
        serverMsg = serverMsg.split(";") #after getting server message, I splitted it
        if serverMsg[0] != "SERVER>>> loginsuccess":
            messagebox.showerror("Error", "Invalid login!")

        else:
            self.master.destroy()
            if serverMsg[2] == "librarian":
                window = Librarian(userName)
                window.mainloop()
            elif serverMsg[2] == "manager":
                window = Manager()
                window.mainloop()
            else:
                exit(1)






class Librarian(Frame):

    def __init__(self, librarianName):
        Frame.__init__(self)
        self.librarianName = librarianName
        self.pack()
        self.master.title("Librarian Panel")
        self.master.geometry("400x600")

        self.frame1 = Frame(self)
        self.frame1.pack(padx=5, pady=5)

        self.titleLabel = Label(self.frame1, text="Books")
        self.titleLabel.pack(padx=5, pady=5)

        self.frame2 = Frame(self)
        self.frame2.pack(padx=5, pady=5, expand=YES, fill=BOTH)

        bookFile = open("books.txt", "r")
        fileData = bookFile.readlines()[1:]
        bookData = []
        for line in fileData:
            bookData.append(line.strip("\n").split(";"))


        self.bookDict = {}  # keys are unique IDs, values are bookName + author
        for bookInfo in bookData:
            nameAndAuthorTuple = (bookInfo[1] + " by " + bookInfo[2], BooleanVar())
            self.bookDict[bookInfo[0]] = nameAndAuthorTuple

        for bookID,nameAndAuthor in self.bookDict.items():
            self.selectBookName = Checkbutton(self.frame2, anchor=W, text=nameAndAuthor[0], variable=nameAndAuthor[1])
            self.selectBookName.pack(expand=YES, fill=BOTH, padx=5, pady=5)

        self.frame3 = Frame(self)
        self.frame3.pack(padx=5, pady=5)

        self.dateLabel = Label(self.frame3, text="Date(dd.mm.yyyy):")
        self.dateLabel.pack(side=LEFT, padx=5, pady=5)

        self.dateEntry = Entry(self.frame3, name="date entry")
        self.dateEntry.pack(padx=5, pady=5)

        self.frame4 = Frame(self)
        self.frame4.pack(padx=5, pady=5)

        self.clientUsernameLabel = Label(self.frame4, text="Client's name:")
        self.clientUsernameLabel.pack(side=LEFT, padx=5, pady=5)

        self.clientUsernameEntry = Entry(self.frame4, name="name entry")
        self.clientUsernameEntry.pack(padx=5, pady=5)

        self.frame5 = Frame(self)
        self.frame5.pack(padx=5, pady=5)

        self.rentButton = Button(self.frame5, text="Rent", command=self.pressedRent)
        self.rentButton.pack(side=LEFT, padx=5,pady=5)

        self.returnButton = Button(self.frame5, text="Return", command=self.pressedReturn)
        self.returnButton.pack(side=LEFT, padx=5, pady=5)

        self.closeButton = Button(self.frame5, text="Close", command=self.pressedClose)
        self.closeButton.pack(side=LEFT, padx=5, pady=5)

    def pressedRent(self):

        librarianName = self.librarianName
        clientUsername = self.clientUsernameEntry.get()
        date = self.dateEntry.get()
        rentedBookIDs = ""
        for bookID,nameAndAuthor in self.bookDict.items():
            if nameAndAuthor[1].get():
                rentedBookIDs += ";" + str(bookID)
        clientMsg = "rent;" + librarianName + ";" + clientUsername + ";" + date + rentedBookIDs
        msg = ("CLIENT>>> " + clientMsg).encode()
        clientSocket.send(msg)
        serverMsg = clientSocket.recv(1024).decode()
        print(serverMsg)
        serverMsg = serverMsg.split(";")

        if serverMsg[0] == "SERVER>>> availabilityerror":
            notAvailableBookIDs = serverMsg[1:]
            notAvailableBookNameAndAuthor = []
            for id in notAvailableBookIDs:
                notAvailableBookNameAndAuthor.append(self.bookDict[id][0])
            messagebox.showerror("Error","Book(s) that you want to rent is not available:\n" + "\n".join(notAvailableBookNameAndAuthor))

        elif serverMsg[0] == "SERVER>>> renterror":
            mustReturnedBookIDs = serverMsg[1:]
            mustReturnedBookNameAndAuthor = []
            for id in mustReturnedBookIDs:
                mustReturnedBookNameAndAuthor.append(self.bookDict[id][0])
            messagebox.showerror("Error", "You need to first return these book(s) before new rent operation: \n" + "\n".join(mustReturnedBookNameAndAuthor))

        elif serverMsg[0] == "SERVER>>> rentsuccess":
            messagebox.showinfo("Message", "Rent operation is done successfuly!")
        else:
            exit()



    def pressedReturn(self):
        librarianName = self.librarianName
        clientUsername = self.clientUsernameEntry.get()
        date = self.dateEntry.get()
        returnedBookIDs = ""
        for bookID, nameAndAuthor in self.bookDict.items():
            if nameAndAuthor[1].get():
                returnedBookIDs += ";" + str(bookID)

        clientMsg = "return;" + librarianName + ";" + clientUsername + ";" + date + returnedBookIDs
        msg = ("CLIENT>>> " + clientMsg).encode()
        clientSocket.send(msg)
        serverMsg = clientSocket.recv(1024).decode()
        print(serverMsg)
        serverMsg = serverMsg.split(";")


        if serverMsg[0] == "SERVER>>> returnerror":
            returnErrorBookIDs = serverMsg[1:]
            returnErrorBookNameAndAuthor = []

            for id in returnErrorBookIDs:
                returnErrorBookNameAndAuthor.append(self.bookDict[id][0])

            #here, even user can return the book s/he rented before, if s/he tries to return the book(s) s/he not rented any time or already returned, system will give error
            #for example, I rented bookA, but I want to return bookA and bookB together. System will say "you cant return bookA and bookB"
            messagebox.showerror("Error", "You can't return these book(s): \n" + "\n".join(returnErrorBookNameAndAuthor))

        elif serverMsg[0] == "SERVER>>> returnsuccess":
            messagebox.showinfo("Message", "Rent operation is done successfuly!\n" + "You need to pay: " + serverMsg[1] + " TL")

        else:
            exit()



    def pressedClose(self):
        self.master.destroy()



class Manager(Frame):

    def __init__(self):
        Frame.__init__(self)
        self.pack()
        self.master.title("Manager Panel")
        self.master.geometry("550x250")


        self.frame1 = Frame(self)
        self.frame1.pack(padx=5, pady=5)

        self.reportsLabel = Label(self.frame1, text="REPORTS")
        self.reportsLabel.pack(padx=5, pady=5)

        self.frame2 = Frame(self)
        self.frame2.pack(padx=5, pady=5)

        self.libraryReports = [
            "(1) What is the most rented book overall?",
            "(2) Which librarian has the highest number of operations?",
            "(3) What is the total generated revenue by the library?",
            "(4) What is the average rental period for the 'Harry Potter' book?"
        ]

        self.report = StringVar()
        self.report.set(self.libraryReports[0])

        for report in self.libraryReports:
            self.selectReport = Radiobutton(self.frame2, anchor=W, text=report, variable=self.report, value=report)
            self.selectReport.pack(padx=5, pady=5,expand=YES, fill=BOTH)

        self.frame3 = Frame(self)
        self.frame3.pack(padx=5, pady=5, expand=YES, fill=BOTH)

        self.createButton = Button(self.frame3, text="Create", command=self.pressedCreate)
        self.createButton.pack(side=LEFT, padx=5, pady=5, expand=YES, fill=BOTH)

        self.closeButton = Button(self.frame3, text="Close", command=self.pressedClose)
        self.closeButton.pack(padx=5, pady=5)

        bookFile = open("books.txt", "r")
        fileData = bookFile.readlines()[1:]
        bookData = []
        for line in fileData:
            bookData.append(line.strip("\n").split(";"))

        self.bookDict = {}  # keys are unique IDs, values are bookName + author
        for bookInfo in bookData:
            nameAndAuthor = bookInfo[1] + " by " + bookInfo[2]
            self.bookDict[bookInfo[0]] = nameAndAuthor




    def pressedCreate(self):
        report = self.report.get()

        #we assume there is exactly 4 report in the manager panel. So we created our regex based on this number.
        pattern = re.match("(\W)(\d)(\W)",report).group(2) # take the report id , e.g. 1

        clientMsg = "report" + pattern
        msg = ("CLIENT>>> " + clientMsg).encode()
        clientSocket.send(msg)
        serverMsg = clientSocket.recv(1024).decode()
        print(serverMsg)
        serverMsg = serverMsg.split(";")  # after getting server message, I splitted it

        if serverMsg[0] == "SERVER>>> report1":
            mostRentedBookIDs = serverMsg[1:]

            if mostRentedBookIDs == [""]: # this means there is no rent operation in anytime
                messagebox.showerror("Error","No book has been ever rented from this library!")
            else:
                mostRentedBookNameAndAuthor = []

                for id in mostRentedBookIDs:
                    mostRentedBookNameAndAuthor.append(self.bookDict[id])

                messagebox.showinfo("Message","Most rented book(s) overall: \n" + "\n".join(mostRentedBookNameAndAuthor))

        elif serverMsg[0] == "SERVER>>> report2":
            mostOperationLibrarian = serverMsg[1:]

            if mostOperationLibrarian == [""]: # this means there is no rent or return operation in anytime
                messagebox.showerror("Error","No book has been ever rented from or returned to this library!")
            else:
                messagebox.showinfo("Message","Librarian(s) that do most operation is: \n" + "\n".join(mostOperationLibrarian))

        elif serverMsg[0] == "SERVER>>> report3":
            messagebox.showinfo("Message","Total revenue of the library: \n" + serverMsg[1] + " TL")

        elif serverMsg[0] == "SERVER>>> report4":
            messagebox.showinfo("Message","Average rental time for book Harry Potter is: \n" + serverMsg[1] + " days")

    def pressedClose(self):
        self.master.destroy()








HOST = "127.0.0.1"
PORT = 5000

clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    clientSocket.connect((HOST, PORT))
except socket.error:
    print("Connection error!")



serverMsg = clientSocket.recv(1024).decode()
if serverMsg == "SERVER>>> connectionsuccess":
    print(serverMsg)
    window = Login()
    window.mainloop()



    # serverMsg = clientSocket.recv(1024).decode()

else:
    msg = "CLIENT>>> TERMINATE".encode()
    clientSocket.send(msg)
    print("Connection terminated! ")
    clientSocket.close()
