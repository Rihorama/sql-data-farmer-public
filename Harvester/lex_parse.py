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
table_list = []  # list keeping all table objects we create in the process
name_dict = {}  # dictionary that helps reach table object by its name
new_table = None  # the current new table

#attribute variables
attr_list = []  # list of attribute objects for the newest table
new_attribute = None  # current attribute
param_list = []  # data type parameters

alter_table = None  # stores the object while we alter it
alter_attr = None

TO_ADD = ['character varying', 'bit varying']
ADD_VAL = 8  # number to be a generic parameter for types stated above

NUMERIC_INT = 10  # if we get parameterless numeric, we define these parameters
NUMERIC_FRAC = 0  # default frac value for numeric

ARRAY_FLAG = False  # do we have an array attribute?
DIM_CNT = 0  # how many dimensions
DIM_SIZE = []  # size of each dimension

DEFAULT_TIME_PRECISION = 0  # allowed range 0-6 for fractional part of seconds

TO_SET_CONSTR = []  # list of multiple attributes that need to have their new constraint flagged
                            #as the parser doesn't know the constr name the moment he's parsing the attrs

PARAM_COUNTER = 0  # incremented with each new parameter, if greater than 1, group counter needed
GROUP_COUNTER = 1  # this is used to mark a group of attributes together being UNIQUE or PRIMARY KEY
                            #starts with 1

DEFAULT_BIT_CHAR = 8  # default value for character or bit types when no size given


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
def input_lex(lexer):

    f = open('./tempfile', 'r')
    data = f.read()  # reads the file to string

    lexer.input(data)

    while True:
        tok = lexer.token()
        if not tok:
            break      # No more input
        print tok


##
#---------THE PARSER------------
## takes f - file descriptor
def sql_parser(f):

    #----LEXER PART-------
    #list of reserved words
    reserved = {
        'CREATE': 'CREATE',
        'TABLE': 'TABLE',
        'ALTER': 'ALTER',
        'ONLY': 'ONLY',
        'CONSTRAINT': 'CONSTRAINT',
        'REFERENCES': 'REFERENCES',
        'ADD': 'ADD',
        'SEQUENCE': 'SEQUENCE',
        'OWNED': 'OWNED',
        'BY': 'BY',

        'bigint': 'DTYPE_SOLO',  # SOLO: this word alone is a data type
        'bigserial': 'DTYPE_SOLO',
        'bit': 'DTYPE_BOTH_1PARAM',  # BOTH: can be either solo or PART1
        'varying': 'DTYPE_PART2',  # PART2: second part of a two-word data type
        'boolean': 'DTYPE_SOLO',
        'box': 'DTYPE_SOLO',
        'bytea': 'DTYPE_SOLO',
        'character': 'DTYPE_BOTH_1PARAM',  # 1PARAM: one mandatory parameter
        'cidr': 'DTYPE_SOLO',
        'circle': 'DTYPE_SOLO',
        'date': 'DTYPE_SOLO',
        'double': 'DTYPE_PART1',
        'precision': 'DTYPE_PART2',
        'inet': 'DTYPE_SOLO',
        'integer': 'DTYPE_SOLO',
        'interval': 'DTYPE_2PARAM',  # 2PARAM: two ??mandatory parameters -not supported for filling now
        #'line' : 'DTYPE_SOLO',
        'lseg': 'DTYPE_SOLO',
        'macaddr': 'DTYPE_SOLO',
        'money': 'DTYPE_SOLO',
        'numeric': 'DTYPE_SOLO_1PARAM2',  # 1PARAM2: One mandatory set of two params
        'path': 'DTYPE_SOLO',
        'point': 'DTYPE_SOLO',
        'polygon': 'DTYPE_SOLO',
        'real': 'DTYPE_SOLO',
        'smallint': 'DTYPE_SOLO',
        'serial': 'DTYPE_SOLO',
        'text': 'DTYPE_SOLO',
        'time': 'DTYPE_TIMEZONE_PARAM',
        'timestamp': 'DTYPE_TIMEZONE_PARAM',
        'tsquery': 'DTYPE_SOLO',
        'tsvector': 'DTYPE_SOLO',
        'txid_snapshot': 'DTYPE_SOLO',
        'uuid': 'DTYPE_SOLO',
        'xml': 'DTYPE_SOLO',

        'NOT': 'NOT',
        'NULL': 'NULL',  # stands for part 2 or solo
        'PRIMARY': 'PRIMARY',
        'FOREIGN': 'FOREIGN',
        'KEY': 'KEY',
        'UNIQUE': 'UNIQUE',
        'DEFAULT': 'DEFAULT',
        'CHECK': 'CHECK',

    }

    # List of token names.   This is always required
    tokens = [
        'IDENTIFIER',
        'NUMBER',
        'FLOATNUM',
        #'EOL',
        'LPAREN',
        'RPAREN',
        'SEMICOLON',
        'COMMA',
        'PERIOD',
        'LBRACKET',
        'RBRACKET',
        'QUOTE',
        'DQUOTES',
        'CHECKATTR',
        #specially for CHECK attributes that can be anything
        'COLON',

    ] + list(reserved.values())

    # Tokens
    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_SEMICOLON = r';'
    t_COMMA = r','
    t_PERIOD = r'\.'
    t_LBRACKET = r'\['
    t_RBRACKET = r'\]'
    t_QUOTE = r'\''
    t_DQUOTES = r'"'
    t_CHECKATTR = r'(\(\()(.*)(\)\))'
    t_COLON = r'\:'

    # A rule for Identifier tokens
    def t_IDENTIFIER(t):
        r'[a-zA-Z][a-zA-Z_0-9]*'
        t.type = reserved.get(
            t.value, 'IDENTIFIER')    # Check for reserved words
        return t

        # A regular expression rule for floating point numbers
    def t_FLOATNUM(t):
        r'(\-)?\d+\.\d+([Ee](\-)?\d+)?'
        t.value = float(t.value)
        return t

    # A regular expression rule for numbers
    def t_NUMBER(t):
        r'(\-)?\d+'
        t.value = int(t.value)
        return t

    #def t_CHARSEQ(t):
    #    r'.*[^\']'

    # A rule for New Line - to tokenize and count as well
    def t_EOL(t):
        r'\n'
        t.lexer.lineno += len(t.value)
    #    return t

    # A string containing ignored characters (spaces and tabs)
    t_ignore = ' \t'

    # Error handling rule
    def t_error(t):
        print ("Not supported character '%s' at line '%s'" % (
            t.value[0], t.lineno))
        exit()
        global err
        err = True  # sets the flag

        t.lexer.skip(1)

    #ignore stderr for a short while
    original_stderr = sys.stderr  # keep a reference to STDERR
    sys.stderr = NullDevice()  # redirect the real STDERR

    # Build the lexer
    lexer = lex.lex()  # will be case insensitive

    #input_lex(lexer)

    #getting ol'stderr back
    sys.stderr = original_stderr

    global err
    if err:
        exit()

    #------PARSER PART--------
    #Rules
    def p_root(p):
        'root : tableBlock moreBlocks moreAlterBlocks'
        debug("dsl")

    def p_moreBlocks(p):
        '''moreBlocks : moreBlocks tableBlock
                      | empty'''
        debug("moreBlocks")

        global table_list
        global new_table

        table_list.append(new_table)

    def p_tableBlock(p):
        'tableBlock : tableHeader attributeBlock moreAttributes moreCheckBlocks RPAREN SEMICOLON moreSequenceBlocks'
        debug("tableBlock")

    def p_moreAttributes(p):
        '''moreAttributes : moreAttributes attributeBlock
                          | empty'''
        debug("moreAttributes")

    def p_tableHeader(p):
        'tableHeader : CREATE TABLE IDENTIFIER LPAREN'
        debug("tableHeader")

        global new_table
        global name_dict

        new_table = table.Table()  # creates new table instance
        new_table.name = p[3]

        name_dict[new_table.name] = new_table

    def p_attributeBlock(p):
        '''attributeBlock : attributeName dtypes COMMA
                          | attributeName dtypes constraintPart COMMA
                          | attributeName dtypes
                          | attributeName dtypes constraintPart'''
        debug("attributeBlock")

        global new_table
        global new_attribute

        new_attribute.name = p[1]
        new_table.attr_list.append(new_attribute)

    def p_attributeName(p):
        '''attributeName : IDENTIFIER
                         | dtypeNames
                         | DQUOTES IDENTIFIER DQUOTES
                         | DQUOTES dtypeNames DQUOTES'''
        debug("attributeName")

        if len(p) == 2:
            p[0] = p[1]  # we pass the attribute name
        else:
            p[0] = p[2]

    #moreDimensions stands for possible array
    def p_dtypes(p):
        '''dtypes : dtype moreDimensions'''

        debug("dtypes")

        global new_attribute
        global param_list

        global ARRAY_FLAG
        global DIM_CNT
        global DIM_SIZE

        new_attribute = table.Attribute()
        new_attribute.data_type = p[1]
        new_attribute.parameters = param_list

        if ARRAY_FLAG:
            new_attribute.array_flag = True
            new_attribute.array_dim_cnt = DIM_CNT
            new_attribute.array_dim_size = DIM_SIZE

            ARRAY_FLAG = False  # iniciates them for next attributes
            DIM_CNT = 0
            DIM_SIZE = []

    def p_dtype(p):
        '''dtype : dtypeSolo
                 | dtypeTwopart
                 | dtypeTimezone'''
        debug("dtype")
        p[0] = p[1]

    #for attr name same as data type purpose
    def p_dtypeNames(p):
        '''dtypeNames : DTYPE_SOLO
                      | DTYPE_BOTH_1PARAM
                      | DTYPE_SOLO_1PARAM2
                      | DTYPE_TIMEZONE_PARAM
                      | DTYPE_PART2
                      | DTYPE_PART1'''
        debug("dtypeNames")
        p[0] = p[1]

    def p_dtypeSolo(p):
        '''dtypeSolo : DTYPE_SOLO
                     | DTYPE_BOTH_1PARAM
                     | DTYPE_SOLO_1PARAM2
                     | DTYPE_BOTH_1PARAM LPAREN parameter RPAREN
                     | DTYPE_SOLO_1PARAM2 LPAREN parameter RPAREN
                     | DTYPE_SOLO_1PARAM2 LPAREN parameter COMMA parameter RPAREN'''
        debug("dtypeSolo")

        p[0] = p[1]

        global param_list
        param_list = []  # inicializes param_list

        #NOTE: we add our own limitations to this potentially unlimited numeric
        #      for filling reasons
        if len(p) == 2 and p[1] == "numeric":
            param_list.append(NUMERIC_INT)
            param_list.append(NUMERIC_FRAC)

        elif len(p) == 2 and (p[1] == "bit" or p[1] == "character"):
            param_list.append(DEFAULT_BIT_CHAR)

        if len(p) == 5:  # variant: DTYPE_BOTH_1PARAM LPAREN parameter RPAREN
            param_list.append(p[3])

        elif len(p) == 7:  # variant: DTYPE_SOLO_1PARAM2 LPAREN parameter COMMA parameter RPAREN
            param_list.append(p[3])
            param_list.append(p[5])

    def p_dtypeTwopart(p):
        '''dtypeTwopart : DTYPE_BOTH_1PARAM DTYPE_PART2
                        | DTYPE_PART1 DTYPE_PART2
                        | DTYPE_BOTH_1PARAM DTYPE_PART2 LPAREN parameter RPAREN'''
        debug("dtypeTwopart")

        p[0] = p[1] + ' ' + p[2]
            #creates one string from the two-part name

        global param_list
        param_list = []

        if len(p) == 6:  # variant: DTYPE_BOTH_1PARAM DTYPE_PART2 LPAREN parameter RPAREN
            param_list.append(p[4])

        global TO_ADD
        global ADD_VAL
        if p[0] in TO_ADD and len(param_list) == 0:  # we will add parameter for filling purposes if not given
            param_list.append(
                ADD_VAL)  # -> varchar(8) and varbit(8)

    def p_dtypeTimezone(p):
        '''dtypeTimezone : DTYPE_TIMEZONE_PARAM LPAREN parameter RPAREN
                         | DTYPE_TIMEZONE_PARAM IDENTIFIER DTYPE_TIMEZONE_PARAM IDENTIFIER
                         | DTYPE_TIMEZONE_PARAM LPAREN parameter RPAREN IDENTIFIER DTYPE_TIMEZONE_PARAM IDENTIFIER'''

        #The second DTYPE_TIMEZONE_PARAM token is there because "time" is already a keyword
        #'with' and 'zone' could be keywords but I didn't think it was necessary
        debug("dtypeTimezone")
        p[0] = p[1]
        global param_list
        param_list = []  # inicializes param_list

        #if with/without timezone is missing, it's automatically without
        if len(p) == 5 and p[2] == "(":
            word1 = "without"
            word2 = "time"
            word3 = "zone"
            param_list.append(p[3])  # we append precision

        if len(p) == 5:
            word1 = p[2]
            word2 = p[3]
            word3 = p[4]
            param_list.append(DEFAULT_TIME_PRECISION)  # we append precision
        else:
            word1 = p[5]
            word2 = p[6]
            word3 = p[7]
            param_list.append(p[3])  # we append precision

        st1 = (word1 == "with" or word1 == "without")
        st2 = (word2 == "time")
        st3 = (word3 == "zone")

        if st1 and st2 and st3:  # all true
            if word1 == "with":
                x = "+TMZ"
            else:
                x = "-TMZ"

        param_list.append(x)  # we append with/without code

    def p_moreDimensions(p):
        '''moreDimensions : moreDimensions oneDimension
                          | empty'''

    def p_oneDimension(p):
        '''oneDimension : LBRACKET RBRACKET
                        | LBRACKET NUMBER RBRACKET'''

        global ARRAY_FLAG
        global DIM_CNT
        global DIM_SIZE
        #we must use these variables because the current new_attribute is still the old one

        ARRAY_FLAG = True
        DIM_CNT = + 1

        if len(p) == 4:
            size = p[2]
        else:
            size = None  # appending None will help us keep track to which dimension the size comes
                           #e.g: [][5] - appending only 5 would be mistaken for [5][]

        DIM_SIZE.append(size)

    def p_constraintPart(p):
        '''constraintPart : constraintPart constraints
                          | empty'''

    def p_constraints(p):
        '''constraints : NOT NULL
                       | NULL
                       | UNIQUE
                       | DEFAULT NUMBER retype
                       | DEFAULT FLOATNUM retype
                       | DEFAULT QUOTE QUOTE retype
                       | DEFAULT QUOTE inquote QUOTE retype
                       | DEFAULT LPAREN NUMBER RPAREN retype
                       | DEFAULT LPAREN FLOATNUM RPAREN retype'''
        debug("constraints")

        if p[1] == "NOT":
            constr = p[1] + ' ' + p[2]
        else:
            constr = p[1]

        global new_attribute
        new_attribute.constraint_flag = True
        new_attribute.constraint_cnt += 1  # increments the cnt
        new_attribute.set_constraint(constr)

        if new_attribute.default:

            if len(p) == 6:  # default different than just ''
                new_attribute.default_value = p[3]

            elif len(p) == 4 and p[1] == "DEFAULT":
                new_attribute.default_value = p[2]

    def p_retype(p):
        '''retype : COLON COLON idOrDtypeName
                  | COLON COLON idOrDtypeName idOrDtypeName
                  | empty'''
        debug("retype")

        #this happens sometimes when default value given
        #nothing happens, we don't need any info from here

    def p_parameter(p):
        '''parameter : NUMBER'''
        debug("parameter")

        p[0] = p[1]

    def p_inquote(p):
        '''inquote : NUMBER
                   | IDENTIFIER'''
        debug("inquote")
        p[0] = p[1]

    #deals with additional check constraints
    def p_moreCheckBlocks(p):
        '''moreCheckBlocks : moreCheckBlocks checkBlock
                           | empty'''
        debug("moreCheckBlocks")

    def p_checkBlock(p):
        '''checkBlock : CONSTRAINT IDENTIFIER CHECK CHECKATTR
                      | CONSTRAINT IDENTIFIER CHECK CHECKATTR COMMA'''
        debug("moreCheckBlocks")

    def p_moreSequenceBlocks(p):
        '''moreSequenceBlocks : moreSequenceBlocks sequenceBlock
                              | empty'''
        debug("moreSequenceBlocks")

    #this is our only hint that the given attribute(collumn) is actually a serial data type
    #we must change it back to serial/bigserial so Seeder can fill it properly
    def p_sequenceBlock(p):
        'sequenceBlock : SEQUENCE IDENTIFIER OWNED BY IDENTIFIER PERIOD IDENTIFIER SEMICOLON'

        debug("sequenceBlock")

        #we find the table
        if not p[5] in name_dict.keys():
            msg = "Semantic error: Table '" + p[5] + \
                "'given in ALTER SEQUENCE part couldn't be found.\n"
            errprint(msg, ERRCODE["SEMANTIC"])
        seq_table = name_dict[p[5]]

        name = p[7]  # name of the attribute
        seq_attr = None

        #search for the attribute
        for attr in seq_table.attr_list:
            if attr.name == name:
                seq_attr = attr
                break

        #we didn't find it, there is a prob (shouldn't happen with not-edited dump but you never know)
        if seq_attr is None:
            msg = "Semantic error: Couldn't find the attribute which SEQUENCE '" + p[2] \
                + "' refers to in table '" + p[5] \
                + "' while processing a " + constr + ".\n"
            errprint(msg, ERRCODE["INPUT"])

        #now we simply change the data type to corresponding serial type
        if seq_attr.data_type == "integer":
            seq_attr.data_type = "serial"

        elif seq_attr.data_type == "bigint":
            seq_attr.data_type = "bigserial"

            #any other type that has a filling sequence gets serial dtype
            #gonna get 'DEFAULT' as insert value
        else:
            seq_attr.data_type = "serial"

    def p_moreAlterBlocks(p):
        '''moreAlterBlocks : moreAlterBlocks alterBlock
                           | empty'''
        debug("moreAlterBlocks")

    def p_alterBlock(p):
        'alterBlock : alterHeader alterBody SEMICOLON'

        debug("alterBlock")

    def p_alterHeader(p):
        'alterHeader : ALTER TABLE ONLY IDENTIFIER'
        debug("alterHeader")

        global alter_table
        if not p[4] in name_dict.keys():
            msg = "Input error: Table '" + p[4] + \
                "'given in ALTER part couldn't be found.\n"
            errprint(msg, ERRCODE["INPUT"])
        alter_table = name_dict[p[4]]

    def p_alterBody(p):
        '''alterBody : ADD CONSTRAINT IDENTIFIER PRIMARY KEY LPAREN idOrDtypeName RPAREN
                     | ADD CONSTRAINT IDENTIFIER FOREIGN KEY LPAREN idOrDtypeName RPAREN REFERENCES IDENTIFIER LPAREN IDENTIFIER RPAREN
                     | multi_attr_constr'''
        debug("alterBody")

        global alter_attr
        global alter_table
        alter_attr = None
        alter_name = None

        #the multi_attr constraint has been solved already
        #this goes just for the KEYs
        if len(p) != 2:

            constr = p[4] + " " + p[5]

            #finding the attribute to get altered
            for attr in alter_table.attr_list:
                if attr.name == p[7]:  # p[7] stands for the attribute name in both cases
                    alter_attr = attr
                    break

            #did we find anything?
            if alter_attr is None:
                msg = "Input error: Couldn't find the given attribute name '" + p[7] \
                    + "' in the list of attributes of table '" + alter_table.name \
                    + "' while processing a " + constr + ".\n"
                errprint(msg, ERRCODE["INPUT"])

            alter_attr.constraint_flag = True
            alter_attr.constraint_cnt += 1  # increments the cnt
            alter_attr.set_constraint(constr)

            #for foreign key
            if p[4] == 'FOREIGN':

                #existence of foreign table check
                if not p[10] in name_dict.keys():
                    msg = "Input error: Foreign table '" + \
                        p[10] + "' couldn't be found.\n"
                    errprint(msg, ERRCODE["INPUT"])

                alter_attr.fk_table = name_dict[p[10]]
                    #gets the foreign table object

                for attr in alter_attr.fk_table.attr_list:
                    if attr.name == p[12]:
                        alter_attr.fk_attribute = attr
                        break

                #existence of foreign attribute check
                if alter_attr.fk_attribute is None:
                    msg = "Input error: Foreign attribute '" + p[12] \
                        + "' couldn't be found in table '" + p[10] \
                        + "' while processing a " + constr + ".\n"
                    errprint(msg, ERRCODE["INPUT"])

    def p_idOrDtypeName(p):
        '''idOrDtypeName : IDENTIFIER
                         | dtypeNames'''
        debug("idOrDtypeName")
        p[0] = p[1]

    #for alters that can apply on more attributes at once
    def p_multi_attr_constr(p):
        '''multi_attr_constr : ADD CONSTRAINT IDENTIFIER UNIQUE LPAREN multi_params RPAREN
                             | ADD CONSTRAINT IDENTIFIER PRIMARY KEY LPAREN multi_params RPAREN'''
        debug("multi_attr_constr")

        global TO_SET_CONSTR
        global GROUP_COUNTER
        global PARAM_COUNTER

        if len(p) == 9:  # two word constraint
            constr = p[4] + " " + p[5]
        else:
            constr = p[4]

        PARAM_COUNTER = len(TO_SET_CONSTR)  # gets size of PARAM_COUNTER so we know how many there are

        #checking if we got more than 1 param. If yes, it means more attributes create a unique group
        for attr in TO_SET_CONSTR:
            attr.set_constraint(
                constr)  # sets flag for each attribute

            if PARAM_COUNTER > 1:  # more than one attribute given as parameter -> group
                attr.unique_group = GROUP_COUNTER  # puts all attributes into the same group
            else:
                attr.unique_group = 0  # single unique attr

        if PARAM_COUNTER > 1:  # if we used the current group number
            GROUP_COUNTER = GROUP_COUNTER + 1  # we increment the counter

        TO_SET_CONSTR = []  # inicialize the set
        PARAM_COUNTER = 0  # and turns param counter back to zero

    #NOTE: For some reason our usually working  'multi_params : multi_params multi_1param'
    #      not working in this case though it should produce the same result as this rule.
    def p_multi_params(p):
        '''multi_params : multi_1param multi_params
                        | empty'''
        debug("multi_params")

    def p_multi_1param(p):
        '''multi_1param : idOrDtypeName COMMA
                        | idOrDtypeName'''
        debug("multi_1param")

        global alter_attr
        global alter_table
        global TO_SET_CONSTR
        global PARAM_COUNTER

        alter_attr = None
        alter_name = None

        #finding the attribute to get altered
        for attr in alter_table.attr_list:
            if attr.name == p[1]:  # p[1] stands for the attribute name in both cases
                alter_attr = attr
                break

        #did we find anything?
        if alter_attr is None:
            msg = "Input error: Couldn't find the given attribute name '" + p[7] \
                + "' in the list of attributes of table '" + alter_table.name \
                + "' while processing a multiparameter ADD CONSTRAINT.\n"
            errprint(msg, ERRCODE["INPUT"])

        alter_attr.constraint_flag = True
        alter_attr.constraint_cnt += 1  # increments the cnt

        TO_SET_CONSTR.append(alter_attr)  # we pass the attribute to alter

    def p_empty(p):
        'empty :'
        pass

    def p_error(p):
        msg = "Syntax error. Trouble with " + repr(str(
            p.value)) + ". Line:" + str(p.lineno) + ".\n"
        errprint(msg, ERRCODE["SYNTACTIC"])
        global err
        err = True  # sets the flag
        #print "Bad function call at line", p.lineno(1)

    #build parser
    yacc.yacc()

    #parse the given file
    yacc.parse(f.read())

    if err:
        exit()

    return table_list  # returns the tables we've recognized
