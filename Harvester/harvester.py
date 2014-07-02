#!/usr/bin/python

import argparse
from dsl_gen import dsl_generator
import lex_parse as parser
from printer import errprint, ERRCODE
import tempfile


###-------------------------
###-------------------------
#Preparses the given dump to leave only things we want
#takes only CREATE TABLE queries and ALTER TABLE ONLY
def preparse(f, tempf):

    starts = ('CREATE TABLE', 'ALTER TABLE ONLY', 'ALTER SEQUENCE')

    create = False  # flag saying that at the moment we are not examining lines of CREATE TABLE query
    alter = False  # nor ALTER TABLE ONLY query
    not_yet = False  # True if we need to wait for semicolon
    query = False

    for line in f:
        li = line.strip()  # get rid of whitespaces on both ends

        if li.startswith(starts):
            query = True  # a query we might want
            save = ""

        if query:

            #if "::character varying" in line:  #NOTE:HOPEFULLY TEMPORAL, I have no idea what is this ::stuff for
            #    line = line.replace("::character varying","")

            save = save + line

            if li.endswith(";"):
                query = False
                #if this alter is not of the ones we want, we continue
                if "ALTER TABLE ONLY" in save and not ("KEY" in save or "UNIQUE" in save):
                    continue

                #it's not alter sequence we want either
                elif "ALTER SEQUENCE" in save and not "OWNED BY" in save:
                    continue

                #we want it, we write it
                else:
                    if "ALTER SEQUENCE" in save:  # because ply yacc we must cut the ALTER word - it causes mess
                            pos = save.find("SEQUENCE")
                            save = save[pos:]
                    tempf.write(save)


###-------------------
###-------------------
DEST = None  # stores user-chosen destination for results (stdout/file)


#arguments
arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("src", help="Path to the source db dump.")
#arg_parser.add_argument("--count" help="Path to the source db dump.")
arg_parser.add_argument('-c', '--count', metavar='N', type=int, help='Fill count to be used for generating. DEFAULT = 10')

group = arg_parser.add_mutually_exclusive_group()
group.add_argument(
    "-s", "--stdout", action="store_true", help="Print to stdout. (DEFAULT)")
group.add_argument("-f", "--file", action="store_true", help="Save as a file.")

args = arg_parser.parse_args()

#none of them was inserted, default = stdout
if not args.file and not args.stdout:
    DEST = "stdout"
if args.file:
    DEST = "file"
else:  # stdout
    DEST = "stdout"

if args.count:
    fill_cnt = args.count
else:
    fill_cnt = 10  # default


#opening given file
try:
    f = open(args.src, 'r')
except IOError:
    msg = "Input error: The given file of path '" + args.src + \
        "' cannot be oppened.\n"
    errprint(msg, ERRCODE["INPUT"])

#opening temp file
try:
    #tempf = open("tempfile", 'w')
    tempf = tempfile.TemporaryFile()
except IOError:
    msg = "Runtime error: Did not manage to create a temporary file 'tempfile'\n."
    errprint(msg, ERRCODE["RUNTIME"])


#Filters the dump so we get only queries we are interested in
preparse(f, tempf)

#Close the dump file
f.close()

#Setting the position to the start of temp file
tempf.seek(0)

#--needed at the moment
#tempf.close()
#try:
#    tempf = open("tempfile", 'r')
#    #tempf = tempfile.TemporaryFile()
#except IOError:
#    msg = "Runtime error: Did not manage to create a temporary file 'tempfile'\n."
#    errprint(msg, ERRCODE["RUNTIME"])
#--needed at the moment


#Parse what's in temp file
table_list = parser.sql_parser(tempf)


#for table in table_list:
#    table.print_table()

#generating the DSL file
dsl_generator(table_list, DEST, fill_cnt)


#Close file
tempf.close()
