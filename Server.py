import copy
import threading
from threading import *
import socket
from datetime import datetime

threadLock = RLock()

class ClientThread(Thread):

    #clientSocket represents connection
    def __init__(self, clientSocket, clientAddress):
        Thread.__init__(self)
        self.clientSocket = clientSocket
        self.clientAddress = clientAddress



    def run(self):

        msg = "SERVER>>> connectionsuccess".encode()
        self.clientSocket.send(msg)
        clientMsg = self.clientSocket.recv(1024).decode()
        originalMessage = copy.deepcopy(clientMsg)
        clientMsg = clientMsg.split(";")

        #user file operations to read the users name and password, and their role
        userFile = open("users.txt", "r")
        fileData = userFile.readlines()[1:] # as the first line of txt is the titles of data, I skip the first line of the txt
        userData = []
        for line in fileData:
            userData.append(line.strip("\n").split(";"))

        # file operations for books.txt to get information about book details, its author, price etc.
        bookFile = open("books.txt", "r")
        fileData = bookFile.readlines()[1:] # as the first line of txt is the titles of data, I skip the first line of the txt
        bookData = []
        for line in fileData:
            bookData.append(line.strip("\n").split(";"))
        bookFile.close()

        #bookDict holds the data of books.txt file.
        self.bookDict = {}  # keys are unique IDs, values are title;authorName;pricePerDay;copiesAvailable
        for bookInfo in bookData:
            self.bookDict[bookInfo[0]] = bookInfo[1:]

        #core loop that we will implement our functions
        while clientMsg[0] != "CLIENT>>> TERMINATE":
            if clientMsg[0] == "CLIENT>>> login":
                print(originalMessage)

                userFound = 0
                userRole = ""
                for user in userData:
                    if clientMsg[1] == user[0] and clientMsg[2] == user[1]:
                        userFound = 1
                        userRole = user[2]
                        break

                if userFound:
                    msg = ("SERVER>>> loginsuccess" + ";" + clientMsg[1] + ";" + userRole).encode()
                else:
                    msg = "SERVER>>> loginfailure".encode()
                self.clientSocket.send(msg)


            elif clientMsg[0] == "CLIENT>>> rent":
                threadLock.acquire()
                try:
                    print(originalMessage)

                    rentedBookIDs = clientMsg[4:]  # take the ID of books which client selected
                    availablityError = 0  # flag indicating we have an availability of book error, if it is 1
                    rentError = 0  # flag indicating that client tries to rent a book(s) without returning books that s/he previously rented
                    rentedBooksFromClient = []  # this holds the ID of book(s) that client rented
                    returnedBooksFromClient = []  # this holds the ID of book(s) that client returned
                    # so the query comes, it is saying that a user named X wants to do rent operation.
                    # to check whether X is returned all her/his books that s/he rented before, we need to check the operations.txt
                    # first we check the rent line with name X, then populate rentedBooksFromClient list with the IDs of book(s) X rented
                    # second we check the return line(s) with name X, then populate returnedBooksFromClient list with the IDs of book(s) X returned
                    # then we take the difference of these two list, for example if l1=["1","2","3"], l2=["1","2"] -> l1-l2 is ["3"]
                    # by doing this, we can see if there is any book that is rented before and not returned!
                    # then we check, if the content of rentedBooks list are empty[]
                    # this means X returned all the books s/he rented before, so allow the new rent operation for this case
                    # else, raise renterror, and do no operation on operations.txt file

                    # file operations for operation.txt to read operations.
                    try:
                        operationsFile = open("operations.txt", "r")
                    except:
                        raise Exception("File could not opened for read")

                    fileData = operationsFile.readlines()[2:]
                    operationsFile.close()  # close the file as we got it's content

                    operationData = []
                    for operation in fileData:
                        operationData.append(operation.strip("\n").split(";"))

                    # hold the IDs of book(s) for both rent and return operation for specific client
                    for operation in operationData:
                        if operation[0] == "rent" and clientMsg[2] == operation[2]:
                            rentedBooksFromClient += operation[4:]
                        if operation[0] == "return" and clientMsg[2] == operation[2]:
                            returnedBooksFromClient += operation[4:]

                    # remove returned book(s) IDs one by one from rented book(s) IDs
                    for bookID in returnedBooksFromClient:
                        if bookID in rentedBooksFromClient:
                            rentedBooksFromClient.remove(bookID)

                    if rentedBooksFromClient == []:  # this means client returned all his/her book(s) before a new rent operation
                        pass
                    else:  # this means s/he did not returned all the book(s) s/he rented before, so raise renterror flag
                        rentError = 1
                        msg = ("SERVER>>> renterror;" + ";".join(rentedBooksFromClient)).encode()
                        self.clientSocket.send(msg)

                    notAvailableBookIDs = []
                    # in this loop, we simply check whether the books are available or not
                    for bookID in rentedBookIDs:  # I get the bookID of the client's rented booksID
                        availablity = int(self.bookDict[bookID][3])  # check the #of copies of book with bookID
                        if availablity != 0:  # this means book with this ID has a copy
                            pass
                        else:  # this means, the book with this ID has 0 copy, so server send an error message,and no operation will be done
                            availablityError = 1
                            notAvailableBookIDs.append(bookID)

                    if not availablityError:  # if every book is available with searched ID, then book(s) are avaiable
                        pass
                    else:
                        msg = ("SERVER>>> availabilityerror;" + ";".join(notAvailableBookIDs)).encode()
                        self.clientSocket.send(msg)

                    if not availablityError and not rentError:  # this means there is no error, so we can update operations.txt
                        msg = "SERVER>>> rentsuccess".encode()
                        self.clientSocket.send(msg)
                        for bookID in rentedBookIDs:
                            availablity = int(self.bookDict[bookID][3])
                            availablity -= 1  # decrement the copy number by 1
                            self.bookDict[bookID][3] = str(availablity)  # store the final #of copy of book
                        # file operations for operation.txt to write operations. I used append to update the txt data each time, so I will not lose previous data in this way

                        try:
                            operationsFile = open("operations.txt", "a")
                        except:
                            raise Exception("File could not opened for write")

                        operationsFile.write(
                            "\nrent;" + clientMsg[1] + ";" + clientMsg[2] + ";" + clientMsg[3] + ";" + ";".join(
                                rentedBookIDs))
                        operationsFile.close()

                finally:
                    threadLock.release()


            elif clientMsg[0] == "CLIENT>>> return":
                threadLock.acquire()
                try:
                    print(originalMessage)

                    # file operations for operation.txt to read operations.
                    try:
                        operationsFile = open("operations.txt", "r")
                    except:
                        raise Exception("File could not opened for read")

                    fileData = operationsFile.readlines()[2:]
                    operationsFile.close()  # close the file as we got it's content

                    operationData = []
                    for operation in fileData:
                        operationData.append(operation.strip("\n").split(";"))

                    rentedBooksFromClient = [] #get the IDs of books that client rent before
                    returnedBooksFromClient = []
                    # hold the IDs of book(s) for both rent and return operation for specific client
                    for operation in operationData:
                        if operation[0] == "rent" and clientMsg[2] == operation[2]:
                            rentedBooksFromClient += operation[4:]
                        if operation[0] == "return" and clientMsg[2] == operation[2]:
                            returnedBooksFromClient += operation[4:]



                    returnBookIDQuery = clientMsg[4:] # this is the clientMessage that client wants to return the books with these IDs
                    returnError = 0 #this flag indicates whether client returns a book(s) which  s/he not rented at anytime or returned already


                    #the idea is that, imagine, client rented book with ID1 and ID2
                    #rentedBooksFromClient contains ID 1 and 2, returnedBooksFromClient contains the ID(s) of return query coming from client
                    #set(rentedBooksFromClient) - set(returnedBooksFromClient) represent the ID(s) of book that is not returned
                    #If all books are returned, then this difference equals to empty list "[]"
                    #If there is still books that are not returned, then this difference list holds that ID(s) of books that are not returned yet
                    #then I will compare this difference with the returned bookIDs message coming from client
                    #If the returnBookIDQuery is not a subset of notReturnedBookIDs, then this means there is an error here
                    #else, this means client wants to return a book(s) that are rented before, and wanted to return now

                    # remove returned book(s) IDs one by one from rented book(s) IDs
                    for bookID in returnedBooksFromClient:
                        if bookID in rentedBooksFromClient:
                            rentedBooksFromClient.remove(bookID)

                    rentedBooksFromClient = set(rentedBooksFromClient)
                    returnBookIDQuery = set(returnBookIDQuery)


                    if  not returnBookIDQuery.issubset(rentedBooksFromClient):
                        # this means s/he try to  return  book(s) s/he not rented before, so sent an error message to client
                        returnBookIDQuery = list(returnBookIDQuery)
                        msg = ("SERVER>>> returnerror;" + ";".join(returnBookIDQuery)).encode()
                        self.clientSocket.send(msg)
                    else:
                        # this means client does not try to return a book that is not rented  by her/him or s/he not returned the rented book yet
                        #so that we can write the return operation with the cost it takes, then send successfull message with the cost

                        #our algorithm to calculate the date difference: take the last rent operation's date and subtract it from the return date of the book
                        # to avoid from previous rents, read the operations.txt from backwards. After read from backwards,
                        # the first rent operation must be the one, which is up-tdate rent operation of the book that client wants to return.
                        #So we can get it's date. After taking the dates, we get the cost of the returned book from self.bookDict, then
                        #evaluate the cost.Finally, we write the return operation into txt file, increment the #of copy of the returned book,
                        #and send a returnsuccessful message to client with the rent cost of the book after returning it.


                        # file operations for operation.txt to read operations.
                        try:
                            operationsFile = open("operations.txt", "r")
                        except:
                            raise Exception("File could not opened for read")

                        fileData = operationsFile.readlines()[:1:-1] #this time, read in backwards
                        operationsFile.close()  # close the file as we got it's content

                        operationData = []
                        for operation in fileData:
                            operationData.append(operation.strip("\n").split(";"))


                        for operation in operationData:
                            if operation[0] == "rent" and operation[2] == clientMsg[2] and returnBookIDQuery.issubset(rentedBooksFromClient):
                                rentDate = operation[3] #get the book's rent date
                                break

                        returnDate = clientMsg[3] # get the date which is returning date of the book

                        rent_date = datetime.strptime(rentDate, "%d.%m.%Y")
                        return_date = datetime.strptime(returnDate, "%d.%m.%Y")
                        difference_in_days = (return_date - rent_date).days # calculate the book(s) rented date to calculate cost
                        #it is assumed that user cant enter a return date that is past from rent date
                        #for example, client rent a book at 05.11.2023, so s/he cant return the book at date 02.05.2022 etc.
                        #This will not give an error, and write negative cost into operations.txt
                        #so it should be better entering dates carefully as a librarian :)

                        rentCost = 0.0

                        for bookID in returnBookIDQuery: #get the each ID(s) to calculate the cost
                            cost = float(self.bookDict[bookID][2]) * int(difference_in_days)
                            rentCost += cost # calculate the rentCost

                        # file operations for operation.txt to write operations. I used append to update the txt data each time, so I will not lose previous data in this way

                        try:
                            operationsFile = open("operations.txt", "a")
                        except:
                            raise Exception("File could not opened for write")

                        operationsFile.write("\nreturn;" + clientMsg[1] + ";" + clientMsg[2] + ";" + clientMsg[3] + ";" + str(rentCost) + ";" + ";".join(returnBookIDQuery))
                        operationsFile.close()

                        #increment the copy of the book(s) that are returned by one
                        for bookID in returnBookIDQuery:
                            availablity = int(self.bookDict[bookID][3])
                            availablity += 1  # decrement the copy number by 1
                            self.bookDict[bookID][3] = str(availablity)  # store the final #of copy of book

                        msg = ("SERVER>>> returnsuccess;" + str(rentCost)).encode()
                        self.clientSocket.send(msg)

                finally:
                  threadLock.release()


            elif clientMsg[0] == "CLIENT>>> report1":
                    print(originalMessage)

                    try:
                        operationsFile = open("operations.txt", "r")
                    except:
                        raise Exception("File could not opened for read")

                    fileData = operationsFile.readlines()[2:] #this time, read in backwards
                    operationsFile.close()  # close the file as we got it's content

                    operationData = []
                    for operation in fileData:
                        operationData.append(operation.strip("\n").split(";"))

                    report1Dict = {} #this is a helper dict. It has key:bookID, value as rent count of book
                    # we assume there is exactly 10 book in the library. So we created our dict based on this number.
                    for i in range(1,11):
                        report1Dict[i] = 0 # set the rent count initialy as 0

                    rentBookAnytime = 0 # this indicates whether a book is rented from library in all time
                    for operation in operationData:
                        if operation[0] == "rent":
                            rentBookAnytime = 1 # if we enter here, this means at least one book is rented
                            rentedBookIDs = operation[4:]
                            for bookID in rentedBookIDs:
                                report1Dict[int(bookID)] += 1

                    mostRentedBookIDs = [] #holds the ID of most rented book(s)

                    if not rentBookAnytime: #this means there is no rent operation, return empty list[] as IDs
                        msg = ("SERVER>>> report1;" + ";".join(mostRentedBookIDs)).encode()
                        self.clientSocket.send(msg)

                    else:
                        mostRentedBook = -1
                        for key,value in report1Dict.items():
                            if report1Dict[key] > mostRentedBook:
                                mostRentedBook =report1Dict[key]


                        for key,value in report1Dict.items():
                            if report1Dict[key] == mostRentedBook:
                                mostRentedBookIDs.append(str(key))

                        msg = ("SERVER>>> report1;" + ";".join(mostRentedBookIDs)).encode()
                        self.clientSocket.send(msg)


            elif clientMsg[0] == "CLIENT>>> report2":
                print(originalMessage)

                try:
                    operationsFile = open("operations.txt", "r")
                except:
                    raise Exception("File could not opened for read")

                fileData = operationsFile.readlines()[2:]  # this time, read in backwards
                operationsFile.close()  # close the file as we got it's content

                operationData = []
                for operation in fileData:
                    operationData.append(operation.strip("\n").split(";"))

                report2Dict = {}  # this is a helper dict. It has key:librarianName, value as rent or return count

                for operation in operationData:
                    if operation[1] not in report2Dict.keys():
                        report2Dict[operation[1]] = 0  # set the operation count initialy as 0


                rentOrReturnBookAnytime = 0  # this indicates whether a book is rented or returned from library in all time
                for operation in operationData:
                    if operation[0] == "rent" or operation[0] =="return":
                        rentOrReturnBookAnytime = 1  # if we enter here, this means at least one book is rented
                        report2Dict[operation[1]] += 1

                mostOperationLibrarian = []  # holds the name of the librarian(s) that do(es) the most operation

                if not rentOrReturnBookAnytime:  # this means there is no rent operation, return empty list[] as IDs
                    msg = ("SERVER>>> report2;" + ";".join(mostOperationLibrarian)).encode()
                    self.clientSocket.send(msg)

                else:
                    mostOperaionCount = -1
                    for key, value in report2Dict.items():
                        if report2Dict[key] > mostOperaionCount:
                            mostOperaionCount = report2Dict[key]

                    for key, value in report2Dict.items():
                        if report2Dict[key] == mostOperaionCount:
                            mostOperationLibrarian.append(key)

                    msg = ("SERVER>>> report2;" + ";".join(mostOperationLibrarian)).encode()
                    self.clientSocket.send(msg)





            elif clientMsg[0] == "CLIENT>>> report3":
                print(originalMessage)

                try:
                    operationsFile = open("operations.txt", "r")
                except:
                    raise Exception("File could not opened for read")

                fileData = operationsFile.readlines()[2:]  # this time, read in backwards
                operationsFile.close()  # close the file as we got it's content

                operationData = []
                for operation in fileData:
                    operationData.append(operation.strip("\n").split(";"))

                totalRevenue = 0.0
                for operation in operationData:
                    if operation[0] == "return":
                        totalRevenue += float(operation[4])

                msg = ("SERVER>>> report3;" + str(totalRevenue)).encode()
                self.clientSocket.send(msg)

            elif clientMsg[0] == "CLIENT>>> report4":
                print(originalMessage)

                try:
                    operationsFile = open("operations.txt", "r")
                except:
                    raise Exception("File could not opened for read")

                fileData = operationsFile.readlines()[2:]  # this time, read in backwards
                operationsFile.close()  # close the file as we got it's content

                operationData = []
                for operation in fileData:
                    operationData.append(operation.strip("\n").split(";"))

                harryPotterCount = 0 # this is the count of how many times this book is rented and returned
                #for example, if I rent this book and return later, the count will be 1
                rentDates = [] #holds the rent dates of book harry potter
                returnDates= [] #holds the return dates of book harry potter

                for operation in operationData:
                    bookIDs = operation[4:]
                    for bookID in bookIDs:
                        if bookID == "3" and operation[0] == "rent": # if the ID of the book is 3, this means the book is HP
                            rentDates.append(operation[3])
                        elif bookID == "3" and operation[0] == "return":
                            returnDates.append(operation[3])
                            harryPotterCount += 1 #if this book is successfully returned, this means it is rentd before, so increment counter



                rentalPeriodOfHP = 0 #indicates the rental period for the "Harry Potter" book
                #if the length of returnDates are 1 less than rentDates, this indicates that this book is rented, but not returned yet
                if len(rentDates) != len(returnDates):
                    #so I pop the last date from rentDates
                    rentDates.pop(-1)

                for i in range(len(returnDates)):
                    rent_date = datetime.strptime(rentDates[i], "%d.%m.%Y")
                    return_date = datetime.strptime(returnDates[i], "%d.%m.%Y")
                    difference_in_days = (return_date - rent_date).days  # calculate the book(s) rented date to calculate cost
                    rentalPeriodOfHP += difference_in_days


                try:
                    averageRentalPeriodOfHP = round(float(rentalPeriodOfHP / harryPotterCount), 2)
                except ZeroDivisionError:
                    averageRentalPeriodOfHP = 0.0


                msg = ("SERVER>>> report4;" + str(averageRentalPeriodOfHP)).encode()
                self.clientSocket.send(msg)

            else:
                exit(1)

            clientMsg = self.clientSocket.recv(1024).decode()
            originalMessage = copy.deepcopy(clientMsg)
            clientMsg = clientMsg.split(";")




        msg = "SERVER>>> TERMINATE".encode()
        self.clientSocket.send(msg)
        print("Connection terminated - ", self.clientAddress)
        self.clientSocket.close()








HOST = "127.0.0.1"
PORT = 5000

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

try:
    serverSocket.bind((HOST, PORT))
except socket.error:
    print("Connection failed!")
    exit(1)
print("Waiting for connections")
while True:
    serverSocket.listen()
    clientSocket, clientAddress = serverSocket.accept()
    newThread = ClientThread(clientSocket, clientAddress)
    newThread.start()