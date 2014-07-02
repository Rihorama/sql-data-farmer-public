import sys


#TODO: check the syntax ret val
ERRCODE = {
    "OK": 0,
    "INPUT": 1,
    "LEXICAL": 2,
    "SYNTACTIC": 3,
    "SEMANTIC": 4,
    "RUNTIME": 5,
    }


##
#Debug printer
##
def debug(msg):

    #print msg
    pass


##
#ERROR printer
##
def errprint(message, ret_value):

    sys.stderr.write(message)
    sys.exit(ret_value)
