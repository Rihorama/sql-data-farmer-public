
import os
import class_table
import exrex
import random
import sys
from method_textbank import fm_textbank
from printer import errprint
from printer import ERRCODE

FOUR_BYTE_MAX = 2147483647
TWO_BYTE_MAX = 32767
EIGHT_BYTE_MAX = 9223372036854775807

CURRENT_MAX = None  # set according to integer type comming to one of the values above

POINT_MAX = 9  # our maximum for point's integer part

PATH_POINTS_MAX = 9  # how many points can path have (-1, not counting starting point)

RADIUS_MAX = 10


#minumum to work for sure according to the postgreSQL docu
FLOAT_MAX = 1e37
FLOAT_MIN = 1e-37

DOUBLE_MAX = 1e308
DOUBLE_MIN = 1e-307


TIMEZONE = [
    "AST",
    "CST",
    "EST",
    "PST",
    "CET",
    "EET",
    "GMT",
    "WET",
    "MSK",
]


# Max range lower than 8: one word will be generated in this range.
# Max range greater or equal to 8: more words generated.
# Vowels and consonants take turns to be at least readable.
# Least possible length is 2 characters.
def basic_varchar(table, attr):

    if not attr.parameters:
        msg = "Internal error: Parameter of attribute " + \
            attr.name + "'s data type disappeared. Sorry for that.\n"
        errprint(msg, ERRCODE["INTERNAL"])

    max_range = attr.parameters[0]  # the only param states the max range
    min_range = 2

    #to prevent provoking users
    if max_range == 1:
        min_range = 1

    #adjusting the max range
    if max_range > 10:
        max_range = 10

    #regex = r'[BCDFGHJKLMNPQRSTVWXZ][aeiouy]([bcdfghjklmnpqrstvwxz][aeiouy])+'
    regex = r'[BCDFGHJKLMNPQRSTVWXZ][aeiouy]([bcdfghjklmnpqrstvwxz][aeiouy][bcdfghjklmnpqrstvwxz]?)+'
    #else:
    #    regex = r'[BCDFGHJKLMNPQRSTVWXZ][aeiouy]([bcdfghjklmnpqrstvwxz][aeiouy]){1,2} (([bcdfghjklmnpqrstvwxz][aeiouy]){1,3})+'

    string = exrex.getone(regex)
    x = random.randint(2, max_range)  # randomly generates varchar length for this iteration from range

    value = string[:x]  # cuts the obtained string

     #checks for white space at the end of string and deletes it if yes
    if string.endswith(' '):
        string = string[:-1]

    return "\'" + value + "\'"  # for string values


#TODO:change error printing here to the one using printer
#returns array of bit values of the given length
def basic_bit(table, attr):

    if not attr.parameters:
        msg = "Internal error: Parameter of attribute " + \
            attr.name + "'s data type disappeared. Sorry for that.\n"
        errprint(msg, ERRCODE["INTERNAL"])

    length = attr.parameters[0]
    regex = '[01]{' + str(length) + '}'

    value = exrex.getone(regex)

    if attr.data_type == "VARBIT":  # we will randomly choose a length between 1 and max
        x = random.randint(1, length-1)
        value = value[:x]

    return value


#Char will be filled with random alfanumerical strings of given length
def basic_char(table, attr):

    if not attr.parameters:
        msg = "Internal error: Parameter of attribute " + \
            attr.name + "'s data type disappeared. Sorry for that.\n"
        errprint(msg, ERRCODE["INTERNAL"])

    length = attr.parameters[0]
    regex = r'[a-zA-Z0-9_]+'

    string = exrex.getone(regex)

    #if the generated string was too short
    while len(string) < length:
        string = string + exrex.getone(regex)

    value = string[:length]  # cuts the obtained string

    return "\'" + value + "\'"


def basic_bool():

    if ((random.randint(0, 9))%2) == 0:  # if random value is even -> True
        value = True
    else:
        value = False

    return value


#positive integer
def basic_int(table, attr):

    flag = True
    regex = r'\d+'
    value = exrex.getone(regex)

    while(int(value) > CURRENT_MAX or int(value) < -CURRENT_MAX):
        value = value[:-1]  # fitting the value to allowed range

    value = int(value)  # removes posible zeros (0025 etc.) This is accepted
                            #but doesn't look so good
    value = str(value)  # reverting back to string
    return value


def basic_text(table, attr):

    path = os.path.dirname(sys.argv[0]) + "/Textbank/sentence.txt"

    if len(attr.fill_parameters) == 0:  # the path hasn't been added yet
        attr.fill_parameters.append(path)  # here we put the textbank path as a parameters so it can use fm_textbank

    value = fm_textbank(table, attr)
    return value


def basic_text(table, attr):

    path = os.path.dirname(sys.argv[0]) + "/Textbank/sentence.txt"

    if len(attr.fill_parameters) == 0:  # the path hasn't been added yet
        attr.fill_parameters.append(path)  # here we put the textbank path as a parameters so it can use fm_textbank

    value = fm_textbank(table, attr)
    return value


#returns (x,y)
def basic_point():

    x = str(random.randint(0, POINT_MAX))  # 0-9
    y = str(random.randint(0, POINT_MAX))

    xflt = random.randint(0, 99)
    yflt = random.randint(0, 99)

    x = str(x) + "." + str(xflt).zfill(2)
            #will ensure two digit length (01,07,10...)
    y = str(y) + "." + str(yflt).zfill(2)

    #50% chance
    minus_x = basic_bool()
    minus_y = basic_bool()

    if minus_x:
        x = "-" + x
    if minus_y:
        y = "-" + y

    return "(" + x + "," + y + ")"

#for line and lseg now


def basic_lseg():

    point1 = basic_point()
    point2 = basic_point()

    return "(" + point1 + "," + point2 + ")"


#not checking possible duplicates among path points
#creates open path
#TODO: do some check for at least the last and first point correspondence maybe?
def basic_path():

    path = basic_point()  # starting point

    x = random.randint(1, PATH_POINTS_MAX)  # variable path length
    for i in range(1, x):
        point = basic_point()
        path = path + "," + point  # extends the path

    return "[" + path + "]"  # brackets indicate open path


#no difference from closed path to be honest
#because I couldn't find if there is any, apart from a different representation
def basic_polygon():

    path = basic_point()  # starting point
    point1 = path

    x = random.randint(1, PATH_POINTS_MAX)  # variable path length
    for i in range(1, x):
        point = basic_point()
        path = path + "," + point  # extends the path

    path = path + "," + point1  # closes the polygon

    return "(" + path + ")"


def basic_circle():

    mid = basic_point()  # getting the center of circle
    radius = random.randint(1, RADIUS_MAX)  # up to 10

    return "<" + str(mid) + "," + str(radius) + ">"


#dor real and double precision
def basic_real(attr_type):

    if attr_type == "REAL":
        exponent = random.randint(-37, 37)  # min and max mantissa
        maximum = FLOAT_MAX
        minimum = FLOAT_MIN

    else:  # double precision
        exponent = random.randint(-307, 308)  # min and max mantissa
        maximum = DOUBLE_MAX
        minimum = DOUBLE_MIN

    #get random mantissa in pattern x.xxx, 3 decimal places max for now
    regex = r'[1-9]\.[0-9]{3}'
    mantissa = exrex.getone(regex)
    value = float(mantissa + "e" + str(exponent))

    if exponent < 0 and value < minimum:
        exponent = + 1  # -37 to -36
        value = float(mantissa + "e" + str(exponent))

    elif exponent > 0 and value > maximum:
        exponent = - 1  # 37 to 36
        value = float(mantissa + "e" + str(exponent))

    return value


def basic_numeric(attr):

    total_cnt = attr.parameters[0]      # = scale = total digits
    fractional_cnt = attr.parameters[1]
        #stands for how many digits are in the fractional part
    integer_cnt = abs(total_cnt - fractional_cnt)

    #now we get random length in that range
    integer_random = random.randint(1, integer_cnt)
    regex = r'[0-9]{' + str(integer_random) + '}'
    integer = exrex.getone(regex)

    value = integer

    #possible fractional part
    if fractional_cnt > 0:
        fractional_random = random.randint(1, fractional_cnt)
        regex = r'[0-9]{' + str(fractional_random) + '}'
        fractional = exrex.getone(regex)

        value = integer + "." + fractional

    return value


#creates network masks with mask /24
def basic_cidr():

    mask = 24

    p1 = random.randint(0, 255)
    p2 = random.randint(0, 255)
    p3 = random.randint(0, 255)
    p4 = 0

    value = str(
        p1) + "." + str(p2) + "." + str(p3) + "." + str(p4) + "/" + str(mask)

    return value


def basic_macaddr():

    value = ""

    #six couples of hexa digits separated by ":"
    for i in range(0, 6):
        value = value + exrex.getone(r'[0-9a-f]{2}') + ":"

    #cuts the last colon
    value = value[:-1]

    return "'" + value + "'"


def basic_date():

    year = str(random.randint(
        1990, 2013))  # most recent years that have passed
    month = str(random.randint(
        1, 12)).zfill(2)  # 1-12 filled with zeros if neccessary: 1 -> 01
    day = random.randint(
        1, 30)  # let's not bother with 31 for now

    if month == "02" and day in range(29, 30):
        day = 28

    day = str(day).zfill(2)
    value = year + "-" + month + "-" + day

    return value


def basic_time(attr):

    hours = str(random.randint(0, 23)).zfill(
        2)  # again filled with zero if it's single digit 1 -> 01
    minutes = str(random.randint(0, 59)).zfill(2)
    seconds = str(random.randint(0, 59)).zfill(2)

    p = attr.parameters[0]
    if p != 0:
        if p > 6:  # if larger number given, we set the largest possible = 6
            p = 6
        regex = '[0-9]{' + str(p) + '}'
        frac = exrex.getone(regex)
        seconds = seconds + "." + \
            frac  # we append the fractional part to seconds

    time = hours + ":" + minutes + ":" + seconds

    if attr.data_type == "TIMESTAMP":
        time = basic_date() + " " + time

    if attr.parameters[1] == "+TMZ":  # timezone wanted
        l = len(TIMEZONE) - 1
        i = random.randint(0, l)
        zone = TIMEZONE[i]

        time = time + " " + zone

    return time


#Basic fill function
#Recognizes the data type and uses it's basic method
def fm_basic(table, attr):

    global CURRENT_MAX

    if attr.data_type == "BIGINT":
        CURRENT_MAX = EIGHT_BYTE_MAX
        value = basic_int(table, attr)

    elif attr.data_type == "BIT" or attr.data_type == "VARBIT":
        value = basic_bit(table, attr)
        if not attr.array_flag:
            value = "bit'" + value + "'"

    elif attr.data_type == "BOOL":
        value = basic_bool()

    elif attr.data_type == "BOX":
        value = basic_lseg()
        if not attr.array_flag:
            value = "box'" + value + "'"

    elif attr.data_type == "CHAR":
        value = basic_char(table, attr)

    elif attr.data_type == "CIDR":
        value = basic_cidr()
        if not attr.array_flag:
            value = "cidr'" + value + "'"

    elif attr.data_type == "CIRCLE":
        value = basic_circle()
        if not attr.array_flag:
            value = "circle'" + value + "'"

    elif attr.data_type == "DATE":
        value = "'" + basic_date() + "'"

    elif attr.data_type == "DOUBLE" or attr.data_type == "REAL":
        value = basic_real(attr.data_type)

    elif attr.data_type == "INET":
        value = basic_cidr()
        if not attr.array_flag:
            value = "inet'" + value + "'"

    elif attr.data_type == "INT":
        CURRENT_MAX = FOUR_BYTE_MAX
        value = basic_int(table, attr)

    #elif attr.data_type == "LINE":
    #    value = "line'" + basic_lseg() + "'"   #not yet implemented in postgre itself

    elif attr.data_type == "LSEG":
        value = basic_lseg()
        if not attr.array_flag:
            value = "lseg'" + value + "'"

    elif attr.data_type == "MACADDR":
        value = basic_macaddr()

    elif attr.data_type == "NUMERIC":
        value = basic_numeric(attr)

    elif attr.data_type == "PATH":
        value = basic_path()
        if not attr.array_flag:
            value = "path'" + value + "'"

    elif attr.data_type == "POINT":
        value = basic_point()
        if not attr.array_flag:
            value = "point'" + value + "'"

    elif attr.data_type == "POLYGON":
        value = basic_polygon()
        if not attr.array_flag:
            value = "polygon'" + value + "'"

    elif attr.data_type == "SMALLINT":
        CURRENT_MAX = TWO_BYTE_MAX
        value = basic_int(table, attr)

    elif attr.data_type == "TEXT":
        value = basic_text(table, attr)

    elif attr.data_type == "TIME":
        value = "'" + basic_time(attr) + "'"

    elif attr.data_type == "TIMESTAMP":
        value = "'" + basic_time(attr) + "'"

    elif attr.data_type == "VARCHAR":
        value = basic_varchar(table, attr)

    return value
