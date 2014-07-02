
from printer import errprint, ERRCODE
import sys
import os


NULL_FILL = 20
DEFAULT_FILL = 20
ARR_SIZE = 3  # default array size if no size given - for fill purposes


DTYPE_DICT = {
    'bigint': 'BIGINT',
    'bigserial': 'BIGSERIAL',
    'bit': 'BIT',
    'bit varying': 'VARBIT',
    'boolean': 'BOOL',
    'box': 'BOX',
    'character varying': 'VARCHAR',
    'character': 'CHAR',
    'cidr': 'CIDR',
    'circle': 'CIRCLE',
    'date': 'DATE',
    'double precision': 'DOUBLE',
    'inet': 'INET',
    'integer': 'INT',
    #'line' : 'LINE',
    'lseg': 'LSEG',
    'macaddr': 'MACADDR',
    'numeric': 'NUMERIC',
    'path': 'PATH',
    'point': 'POINT',
    'polygon': 'POLYGON',
    'real': 'REAL',
    'serial': 'SERIAL',
    'smallint': 'SMALLINT',
    'time': 'TIME',
    'timestamp': 'TIMESTAMP',
    'text': 'TEXT',
    }

#creates a DSL line describing attribute's data type


def get_dtype_line(attr):

    if attr.data_type in DTYPE_DICT.keys():
        line = "\t\tTYPE " + DTYPE_DICT[attr.data_type]
    else:
        line = "\t\tTYPE " + attr.data_type  # not supported types yet

    x = "("
    flag = False

    for param in attr.parameters:
        flag = True
        x = x + str(param) + ","

    x = x[:-1] + ")"
    if flag:
        line = line + x  # appending (parameters..) to the rest

    #array test
    if attr.array_flag:
        for arr in range(0, attr.array_dim_cnt):
            if attr.array_dim_size[arr]:  # if any size given
                dim = "[" + str(attr.array_dim_size[arr]) + "]"
            else:
                dim = "[" + str(ARR_SIZE) + "]"
        line = line + dim  # appends dimensions

    return line


#creates a DSL line describing fill method
def get_fill_line(attr):

    line = "\t\tFILL "

    if attr.foreign_key:
        ref = attr.fk_table.name + ":" + attr.fk_attribute.name
        line = line + "fm_reference(" + ref + ")"
    else:
        line = line + "fm_basic()"

    return line

#TODO: Check constraint compatibility and iniciate their count
#creates a constraint line if necessary


def get_constr_line(attr):

    if not attr.constraint_flag:
        return ""

    line = "\t\tCONSTRAINT "

    if attr.foreign_key:
        line = line + "foreign_key "

    if attr.primary_key:
        if attr.unique_group:
            x = attr.unique_group  # we'll print the group number if given
        else:
            x = 0  # zero stands for UNIQUE/PK alone attributes
        line = line + "primary_key(" + str(x) + ") "

    if attr.unique:
        if attr.unique_group:
            x = attr.unique_group  # we'll print the group number if given
        else:
            x = 0  # zero stands for UNIQUE/PK alone attributes
        line = line + "unique(" + str(x) + ") "

    if attr.null:
        line = line + "null(" + str(NULL_FILL) + ") "

    if attr.not_null:
        line = line + "not_null "

    if attr.default:
        line = line + "default(" + str(DEFAULT_FILL) + ") "
        #if attr.default_value != None:
        #    line = line + "default(" + str(attr.default_value) + ") "
        #else:
        #    line = line + "default('') "

    return line


#A function that generates the dsl file
#according to the given table list
def dsl_generator(table_list, DEST, fill_cnt):

    #iniciates
    initiate_gen(table_list)

    if(DEST == "file"):
        home = os.path.expanduser('~')  # get the home directory for this user
        pth = home + \
            "/dsl.txt"  # creates the path representing ~/dsl.txt
        try:
            fd = open(pth, 'w')
        except IOError:
            msg = "Runtime error: Did not manage to create a destination file '~/dsl.txt'."
            errprint(msg, ERRCODE["RUNTIME"])
    else:
        fd = sys.stdout

    for table in table_list:
        fd.write("TABLE:" + table.name + "(" + str(fill_cnt) + ")\n")

        for attr in table.attr_list:
            fd.write("\t::" + attr.name + "\n")
            fd.write(get_dtype_line(attr) + "\n")
            fd.write(get_fill_line(attr) + "\n")
            fd.write(get_constr_line(attr) + "\n")

        fd.write("\n")

#Does everything necessary for the generator to work
#checks constraint compatibility for each attribute


def initiate_gen(table_list):

    for table in table_list:

        for attr in table.attr_list:

            if attr.constraint_flag and attr.constraint_cnt > 1:
                #TODO:check if unique and primary key can be together
                check1 = attr.unique and attr.primary_key
                check2 = attr.null and attr.primary_key
                check3 = attr.null and attr.not_null

                check = check1 or check2 or check3

                if check:
                    msg = "Input error: Not compatible constraints used for attribute '" \
                          + attr.name + "', table '" + table.name + "'.\n"
                    errprint(msg, ERRCODE["INPUT"])
