
import class_table
import random
import sys
from printer import errprint, ERRCODE

FD = None
OPEN = False
LINECNT = None
ATTRNAME = None


#
#User controlled fill function
#Uses the given path to find and open the textbank file.
#This textbank will be the source for filling the attribute.
#For now using VARCHAR and CHAR.
#Unique and primary keys are solved here because of the iteration timeout.
#Else an infinite loop could occur in cases of smaller textbank than
#fill count. The timeout is for now set to 100.
def fm_textbank(table, attr):

    #opening the file
    if not attr.textbank_open:

        path = attr.fill_parameters[0]

        #opening file
        try:
            attr.textbank_fd = open(path, 'r')

        except IOError:
            msg = "Input error: The given file of path '" + \
                path + "' cannot be oppened."
            errprint(msg, ERRCODE["INPUT"])

        #getting line count
        for i, l in enumerate(attr.textbank_fd):
            pass

        attr.textbank_linecnt = i  # ignores the last line assuming it's empty (else it would be i+1)
        attr.textbank_open = True  # sets the flag

    x = True  # more cycles flag
    timeout = 0

    while x:
        if timeout >= 100:
            msg = "Runtime error: The timeout for finding unique value in given textbank '" + path + "' exceeded."
            errprint(msg, ERRCODE["RUNTIME"])

        x = False
        attr.textbank_fd.seek(0)  # sets at the beginning

        num = random.randint(1, attr.textbank_linecnt)
                             #gets random number from 0 to the line count
        i = 1  # start index

        #cycle to find the right line
        for line in attr.textbank_fd:
            if i == num:  # once we get to the wanted line
                value = line.rstrip(
                    )  # it contains the value we want (cuts the newline)
                break;
            i = i + 1  # increments the index

        #some checking for
        if attr.data_type == "CHAR" or attr.data_type == "VARCHAR":
            length = attr.parameters[0]

            #NOTE: CHAR speciality. The databank is not checked for CHAR length
            #      validity. If not suitable value is received, the received
            #      string is either cut or multiply concatenated and then cut.
            #      Provided textbank is fully at user's responsibility.
            if attr.data_type == "CHAR":

                while len(value) < length:
                    value = value + value

            value = value[:length]  # cuts to the desired size

        #now checking for UNIQUE/PRIMARY KEY
        #if this constraint present, we check the retrieved value
        #for presence in attribute.values_list. If it's not there yet,
        #the value is stored in the list and approved - else we repeat all above
        #This might get very time expensive with textbank method
        #so there is a 100 iterations timeout set
        if attr.constraint_type == "primary_key" or attr.constraint_type == "unique":
            if value in attr.values_list:
                x = True
                timeout += 1

            else:
                break

    attr.textbank_fd.seek(
        0)  # for potential other attributes using the same textbank
    return "'" + value + "'"

#try to close file once the filling ends, called from the values_generator after
#cycling over each table finishes


def textbank_close(table):

    for attr in table.attr_list:
        if attr.textbank_open:
            attr.textbank_fd.close()
            attr.textbank_open = False
