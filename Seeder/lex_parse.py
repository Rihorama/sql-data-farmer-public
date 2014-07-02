#!/usr/bin/python


import sys
import ply.lex as lex
import ply.yacc as yacc
import class_table as table
import re
from printer import debug
from printer import errprint
from printer import ERRCODE


sys.path.insert(0, "../..")


#TODO: Check newlines at the end of every error message

#table variables
table_list = []
new_table = None

#attribute variables
attr_list = []
new_attribute = None

#error flag
err = False


#class to temporarily ignore stderr
#done to hide those ply yacc warnings...
class NullDevice():
    def write(self, s):
        pass


##
#function to see the tokens
##
def input_lex(lexer, fd):

    data = fd.read()  # reads the file to string

    lexer.input(data)

    while True:
        tok = lexer.token()
        if not tok:
            break      # No more input
        print tok


##
#to check possible data type and constraint collisions
##
def check_collision():

    global new_attribute

    if new_attribute.serial:
        if new_attribute.null or new_attribute.foreign_key:
            msg = "Semantic Error: Attribute '" + new_attribute.name + "' has a constraint uncompatible " \
                  + "with its data type '" + new_attribute.data_type + "'. Colliding constraint: " \
                  + new_attribute.constraint_type + ".\n"
            errprint(msg, ERRCODE["SEMANTIC"])


##
#check of valid parameters/constraints/data types for fill method
##
def check_valid(attr):

    method = attr.fill_method
    global new_table

    if method == 'fm_regex':

        #check_regex_compatibility(attr)    #check if regex method can be used with given data type
                                            #edit: let's leave it free for all - on users responsibility
        try:
            re.compile(str(attr.fill_parameters[0]))
                       #check if the given parameter is a valid regex
        except re.error:
            msg = "Semantic Error: Wrong parameter given to fill method '" + new_attribute.fill_method \
                  + "' in table '" + new_table.name + \
                "', attribute '" + new_attribute.name + "'.\n"
            errprint(msg, ERRCODE["SEMANTIC"])

    elif method == 'fm_textbank':
        if not attr.data_type in ("VARCHAR", "CHAR", "TEXT"):

            msg = "Semantic Error: The given fill method '" + new_attribute.fill_method \
                + "' incompatible with the given data type '" + new_attribute.data_type \
                + "' in table '" + new_table.name + \
                "', attribute '" + new_attribute.name + "'.\n"
            errprint(msg, ERRCODE["SEMANTIC"])

    elif method == 'fm_reference':

        string = attr.fill_parameters[0]
        pos = string.find(":")

        if pos == -1:  # didn't find the colon
            msg = "Semantic Error: Wrong parameter given to fill method '" + new_attribute.fill_method \
                + "' in table '" + new_table.name + \
                "', attribute '" + new_attribute.name + "'.\n"
            errprint(msg, ERRCODE["SEMANTIC"])

        new_table.fk = True  # sets the flag that table contains a foreign key
        attr.foreign_key = True  # this flag allows us to fill this attr properly (if different than foreign key data type given, we have to set it here)
        attr.fk_table = string[0:pos]  # gets what is before the colon
        attr.fk_attribute = string[(pos+1):]

        if new_table.name == attr.fk_table:
            msg = "Semantic Error: Foreign key referencing the same table not supported. Table: '" \
                  + new_table.name + "', attribute: '" + attr.name + "'.\n"
            errprint(msg, ERRCODE["SEMANTIC"])

    elif method == 'fm_default':

        if not attr.default:
            msg = "Semantic Error: Fill method fm_default stated but no DEFAULT value given.'.\n"
            errprint(msg, ERRCODE["SEMANTIC"])


##
#function to check if the fm_method is used in combination with allowed data types
##
def check_regex_compatibility(attr):

    if not attr.data_type in ("VARCHAR", "CHAR", "INT"):

        msg = "Semantic Error: The given fill method '" + new_attribute.fill_method \
            + "' incompatible with the given data type '" + new_attribute.data_type \
            + "' in table '" + new_table.name + \
            "', attribute '" + new_attribute.name + "'.\n"
        errprint(msg, ERRCODE["SEMANTIC"])


##
#---------THE PARSER------------
## takes f - file descriptor
def dsl_parser(f):

    #----LEXER PART-------
    #list of reserved words
    reserved = {
        'TABLE': 'TABLE',
        'TYPE': 'TYPE',
        'FILL': 'FILL',
        'CONSTRAINT': 'CONSTRAINT',

        'FILLED': 'FILLED',

        'unique': 'CONSTR_1PARAM',
        'primary_key': 'CONSTR_1PARAM',
        'foreign_key': 'CONSTR_NOPARAM',
        'null': 'CONSTR_1PARAM',
        'default': 'CONSTR_1PARAM',
        'not_null': 'CONSTR_NOPARAM',

        'BIGINT': 'TYPE_NOPARAM',  # INT8
        'BIGSERIAL': 'TYPE_NOPARAM',
        'BIT':     'TYPE_1PARAM',
        'BOOL': 'TYPE_NOPARAM',  # BOOLEAN
        'BOX': 'TYPE_NOPARAM',
        'CHAR': 'TYPE_1PARAM',  # CHARACTER
        'CIDR': 'TYPE_NOPARAM',
        'CIRCLE': 'TYPE_NOPARAM',
        'DATE': 'TYPE_NOPARAM',
        'DOUBLE': 'TYPE_NOPARAM',
        'INET': 'TYPE_NOPARAM',
        'INT': 'TYPE_NOPARAM',  # INTEGER, INT4
        'LSEG': 'TYPE_NOPARAM',
        #'LINE' : 'TYPE_NOPARAM',    #not yet implemented in postgre
        'MACADDR': 'TYPE_NOPARAM',
        'NUMERIC': 'TYPE_2PARAM',
        'PATH': 'TYPE_NOPARAM',
        'POINT': 'TYPE_NOPARAM',
        'POLYGON': 'TYPE_NOPARAM',
        'REAL': 'TYPE_NOPARAM',
        'SERIAL': 'TYPE_NOPARAM',
        'SMALLINT': 'TYPE_NOPARAM',  # INT2
        'TEXT': 'TYPE_NOPARAM',
        'TIME': 'TYPE_2PARAM_TIME',
        'TIMESTAMP': 'TYPE_2PARAM_TIME',
        'VARBIT': 'TYPE_1PARAM',  # BIT VARYING
        'VARCHAR': 'TYPE_1PARAM',  # CHARACTER VARYING

        'fm_basic': 'FILL_METHOD_NOPARAM',
        'fm_regex': 'FILL_METHOD_1PARAM',
        'fm_textbank': 'FILL_METHOD_1PARAM',
        'fm_reference': 'FILL_METHOD_1PARAM',

    }

    # List of token names.   This is always required
    tokens = [
        'IDENTIFIER',
        'NUMBER',
        'DOUBLE_COLON',
        'COLON',
        'EOL',
        'LPAREN',
        'RPAREN',
        'REGEX',
        'PATH',
        'COMMA',
        'LBRACKET',
        'RBRACKET',
        'TIMEZONE_PARAM',
        'QUOTE',
        'BACKSLASH',
    ] + list(reserved.values())

    # Tokens
    t_DOUBLE_COLON = r'\:\:'
    t_COLON = r'\:'
    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_COMMA = r','
    t_LBRACKET = r'\['
    t_RBRACKET = r'\]'
    t_QUOTE = r'\''
    #t_BACKSLASH = r'r[\\@]'
    #t_REGEX = r'r\'[\\ 0-9A-Za-z#\$%=@!\{\},`~\&\*\(\)\<\>\?\.:;_\|\^/+\[\]"\-]*\''
    #t_REGEX = r'r\'[ 0-9A-Za-z#\$%=@!\{\},`~\&\*\(\)\<\>?\.:;_\|\^/+\t\r\n\[\]"\-]*\''
    #([bcdfghjklmnpqrstvwxz][aeiouy]){3}@([bcdfghjklmnpqrstvwxz][aeiouy]){2}\.

    def t_BACKSLASH(t):
        r'\'\\@\''

    def t_TIMEZONE_PARAM(t):
        r'[\+\-]TMZ'
        return t

    # A rule for regular expressions
    def t_REGEX(t):
        r'\'[\\ 0-9A-Za-z#\$%=@!\{\},`~\&\*\(\)\<\>\?\.:;_\|\^/+\[\]"\-]+\''
        return t

    # A rule for Identifier tokens
    def t_IDENTIFIER(t):
        r'[a-zA-Z][a-zA-Z_0-9]*'
        t.type = reserved.get(
            t.value, 'IDENTIFIER')    # Check for reserved words
        return t

    # A regular expression rule for numbers
    def t_NUMBER(t):
        r'(\-)?\d+'
        t.value = int(t.value)
        return t

    # A rule for New Line - to tokenize and count as well
    def t_EOL(t):
        r'\n'
        t.lexer.lineno += len(t.value)
        return t

    # A rule for file path
    def t_PATH(t):
        r'[a-zA-Z_0-9/\-\.]+'
        return t

    # A string containing ignored characters (spaces and tabs)
    t_ignore = ' \t'

    # Error handling rule
    def t_error(t):
        print ("Illegal character '%s' at line '%s'" % (t.value[0], t.lineno))

        global err
        err = True  # sets the flag

        t.lexer.skip(1)

    #ignore stderr for a short while
    original_stderr = sys.stderr  # keep a reference to STDERR
    sys.stderr = NullDevice()  # redirect the real STDERR

    # Build the lexer
    lexer = lex.lex()

    #fd = open("./dsl.txt",'r')
    #input_lex(lexer,fd)

    #getting ol'stderr back
    sys.stderr = original_stderr

    global err
    if err:
        exit()

    #------PARSER PART--------
    #Rules
    def p_dsl(p):
        'dsl : tableBlock moreBlocks'
        debug("dsl")

    def p_moreBlocks(p):
        '''moreBlocks : moreBlocks tableBlock
                      | empty'''

        global new_table
        global attr_list
        new_table.attr_list = attr_list   # adds complete list of attributes
        new_table.count_attributes(
            )      # stores the count of attributes in table.attr_count
        debug("moreBlocks")

    def p_tableBlock(p):
        'tableBlock : tableHeader attributeBlock moreAttributes'
        table_list.append(new_table)
        debug("tableBlock")

    def p_moreAttributes(p):
        '''moreAttributes : moreAttributes attributeBlock
                          | empty'''
        debug("moreAttributes")

    def p_tableHeader(p):
        '''tableHeader : TABLE COLON IDENTIFIER LPAREN NUMBER RPAREN endline
                       | TABLE COLON IDENTIFIER LPAREN FILLED RPAREN endline'''

        global new_table
        new_table = table.Table()  # creates new table instance
        new_table.fill_count = p[5]
        new_table.name = p[3]     # corresponds to the IDENTIFIER token

        global attr_list
        attr_list = []            # inicializes empty list for this table
        debug("tableHeader")

    def p_attributeBlock(p):
        '''attributeBlock : attributeName dataType fillMethod
                          | attributeName dataType fillMethod constraintPart'''

        global new_attribute
        global attr_list

        #first we check compatibility of given functions, parameters and data types
        check_valid(new_attribute)

        #then we check possible data_type and constraint collisions
        check_collision()

        attr_list.append(new_attribute)  # appends the new attribute
        new_attribute.constraint_flag = False  # nulls the flag
        debug("attributeBlock")

    def p_attributeName(p):
        'attributeName : DOUBLE_COLON IDENTIFIER endline'

        global new_attribute
        new_attribute = table.Attribute()  # new attribute instance
        new_attribute.values_list = []
        new_attribute.name = p[2]
        debug("attributeName")

    def p_dataType(p):
        'dataType : TYPE dtypes moreDimensions endline'
        debug("dataType")

    def p_dtypes(p):
        '''dtypes : TYPE_NOPARAM
                  | TYPE_1PARAM LPAREN NUMBER RPAREN
                  | TYPE_2PARAM LPAREN NUMBER COMMA NUMBER RPAREN
                  | TYPE_2PARAM_TIME LPAREN NUMBER COMMA TIMEZONE_PARAM RPAREN'''

        global new_attribute
        global new_table
        new_attribute.data_type = p[1]
        new_attribute.parameters = []  # inicializes to no parameters

        if len(p) == 5:  # stands for "DTYPE (1_param)"
            new_attribute.parameters.append(p[3])  # appends the parameter

        elif len(p) == 7:  # DTYPE_2PARAM
            new_attribute.parameters.append(p[3])
            new_attribute.parameters.append(p[5])

        if p[1] == 'SERIAL' or p[1] == 'BIGSERIAL':
            new_attribute.serial = True

        if p[1] == "TIME":
            print new_attribute.parameters

        debug("dtypes")

    def p_moreDimensions(p):
        '''moreDimensions : moreDimensions oneDimension
                          | empty'''

    def p_oneDimension(p):
        '''oneDimension : LBRACKET NUMBER RBRACKET'''

        global new_attribute
        new_attribute.array_flag = True
        new_attribute.array_dim_size.append(
            p[2])  # p[2] stands for the max size of this array
        new_attribute.array_dim_cnt = len(new_attribute.array_dim_size)

    def p_fillMethod(p):
        '''fillMethod : FILL FILL_METHOD_NOPARAM LPAREN RPAREN endline
                      | FILL FILL_METHOD_1PARAM LPAREN parameter RPAREN endline'''

        global new_attribute
        global new_table
        new_attribute.fill_method = p[2].lower()  # lower case to be sure
        debug("fillMethod")

        if len(p) == 7:  # one parameter
            new_attribute.fill_parameters = []  # clears the list
            new_attribute.fill_parameters.append(p[4])

    def p_constraintPart(p):
        '''constraintPart : CONSTRAINT constr moreConstr endline'''
        debug("constraintPart")

    def p_moreConstr(p):
        '''moreConstr : constr moreConstr
                      | empty'''
        debug("moreConstr")

    def p_constr(p):
        '''constr : CONSTR_NOPARAM
                  | CONSTR_1PARAM LPAREN NUMBER RPAREN'''
        debug("constraintPart")

        global new_attribute

        if p[1] == "foreign_key":
            #new_attribute.foreign_key = True
            return  # like nothing happened, fm_reference sets the flag
        elif p[1] == "primary_key":
            new_attribute.primary_key = True
            new_attribute.unique_group = p[3]
        elif p[1] == "unique":
            new_attribute.unique = True
            new_attribute.unique_group = p[3]
        elif p[1] == "null":
            new_attribute.null = True
            new_attribute.constraint_parameters = p[3]
        elif p[1] == "not_null":
            new_attribute.not_null = True

        elif p[1] == "default":
            new_attribute.default = True

            #if len(p) == 5:
            #    val = p[3]
            #elif len(p) == 6:
            #    val = "''"
            #else:
            #    val = p[4]

            new_attribute.default_value = p[3]  # stores the percentage

        new_attribute.constraint_type = p[1]
        new_attribute.constraint_flag = True
        new_attribute.constraint_cnt += 1

        #TODO:check if it's really neccessary to make generator go more easy, feels chaotic here
        if new_attribute.primary_key:
            new_attribute.unique = True

        #TODO: checkovat, ze neni zadana spatna fill metoda
    def p_parameters(p):
        '''parameters : parameters parameter
                      | empty'''
        debug("parameters")

    def p_parameter(p):
        '''parameter : PATH
                     | REGEX
                     | NUMBER
                     | IDENTIFIER
                     | IDENTIFIER COLON IDENTIFIER'''
        p[0] = p[1]  # returns the value in p[0]
        debug("parameter")

        if len(p) == 4:  # IDENTIFIER COLON IDENTIFIER variant
            p[0] = p[1] + ":" + p[3]
                #concatenates so it can be passed together

    def p_endline(p):
        'endline : EOL extraEndline'
        debug("endline")

    def p_extraEndline(p):
        '''extraEndline : EOL extraEndline
                        | empty'''
        debug("extraEndline")

    def p_empty(p):
        'empty :'
        pass

    def p_error(p):
        msg = "Syntax error. Trouble with " + repr(str(
            p.value)) + " on line " + str(p.lineno) + ".\n"
        errprint(msg, ERRCODE["SYNTACTIC"])
        global err
        err = True  # sets the flag
        #print "Bad function call at line", p.lineno(1)

    #ignore stderr for a short while
    original_stderr = sys.stderr  # keep a reference to STDERR
    sys.stderr = NullDevice()  # redirect the real STDERR

    #build parser
    yacc.yacc()

    #getting ol'stderr back
    sys.stderr = original_stderr

    #parse the given file
    yacc.parse(f.read())

    if err:
        exit()

    return table_list  # returns the tables we've recognized
