#!/usr/bin/python

# -----------------------------------------------------------------------------
# calc.py
#
# A simple calculator with variables.   This is from O'Reilly's
# "Lex and Yacc", p. 63.
# -----------------------------------------------------------------------------

import sys
sys.path.insert(0,"../..")

##
#takes the file descriptor, converts the file to a string and feed the lexer
##
def input_lex(lexer, data):
  
    #data = f.read() #reads the file to string
  
    lexer.input(data)
  
    while True:
        tok = lexer.token()
        if not tok: break      # No more input
        print tok

#list of reserved words
reserved = {
    'TABLE' : 'TABLE',
    'TYPE' : 'TYPE',
    'FILL' : 'FILL',
    'CONSTRAINT' : 'CONSTRAINT'
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
    'NAME'
] + list(reserved.values())

# Tokens

t_DOUBLE_COLON   = r'\:\:'
t_COLON  = r'\:'
t_LPAREN  = r'\('
t_RPAREN  = r'\)'
t_NAME    = r'[a-zA-Z_][a-zA-Z0-9_]*'

# A rule for Identifier tokens
def t_IDENTIFIER(t):
    r'[a-zA-Z][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value,'IDENTIFIER')    # Check for reserved words
    return t

# A regular expression rule for numbers
def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)    
    return t

# A rule for New Line - to tokenize and count as well

def t_EOL(t):
    r'\n'
    t.lexer.lineno += len(t.value)
    return t

# A string containing ignored characters (spaces and tabs)
t_ignore  = ' \t'

# Error handling rule
def t_error(t):
    print "Illegal character '%s'" % t.value[0]
    t.lexer.skip(1)
    
# Build the lexer
import ply.lex as lex
lexer = lex.lex()
data = '''TABLE:tabulka(50)
        ::atribut
        TYPE sedm
        FILL ahaha()
        '''
input_lex(lexer, data)

# Parsing rules


# dictionary of names
names = { }

#def p_statement_assign(p):
#    'statement : TABLE COLON IDENTIFIER LPAREN NUMBER RPAREN EOL'
    
def p_dsl(p):
    'dsl : tableBlock moreBlocks'
    print("DSL")

def p_moreBlocks(p):
    '''moreBlocks : moreBlocks tableBlock
		  | empty'''
    print("moreBlocks")

def p_tableBlock(p):
    'tableBlock : tableHeader attributeBlock'
    print("tableBlock")
		
def p_moreAttributes(p): 
    '''moreAttributes : moreAttributes attributeBlock
			| empty'''  
    print("moreAttributes")

def p_tableHeader(p):
    'tableHeader : TABLE COLON IDENTIFIER LPAREN NUMBER RPAREN EOL'
    print("tableHeader")

def p_attributeBlock(p):
    'attributeBlock : attributeName dataType fillMethod'
    print("attributeBlock")

def p_attributeName(p):
    'attributeName : DOUBLE_COLON IDENTIFIER EOL'
    print("attributeName")

def p_dataType(p):
    'dataType : TYPE IDENTIFIER EOL'
    print("dataType")

def p_fillMethod(p):
    'fillMethod : FILL IDENTIFIER LPAREN parameters RPAREN EOL'
    print("fillMethod")

def p_parameters(p):
    '''parameters : parameters parameter
		    | empty'''
    print("parameters")
		
def p_parameter(p):
    'parameter : IDENTIFIER'
    print("parameter")
    
def p_empty(p):
    'empty :'
    pass
    
def p_error(p): 
    print("Syntax error at '%s'" % p)



import ply.yacc as yacc
yacc.yacc()


yacc.parse('''TABLE:tabulka(50)
        ::atribut
        TYPE sedm
        FILL ahaha()
        ''')
    
    


