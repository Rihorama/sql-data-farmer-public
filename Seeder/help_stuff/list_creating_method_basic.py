
import class_table
import exrex
import random
import sys



# Max range lower than 8: one word will be generated in this range. 
# Max range greater or equal to 8: more words generated.
# Vowels and consonants take turns to be at least readable.
# Least possible length is 2 characters.
def basic_varchar(table, attr):
    
    if not attr.parameters :
        sys.stderr.write("Internal error. Parameter of attribute " + attr.name + " disappeared." \
                         "Recovery not possible, the functionality of Seeder is inconsistent from now on.\n")
        exit()
               
    values = []
    max_range = attr.parameters[0]
    min_range = 2
    
    #to prevent provoking users
    if max_range == 1:
        min_range = 1
    
    
    #the regular expression to be used will be chosen according to the max range
    if max_range < 8:     #product will be one word
        regex = r'[BCDFGHJKLMNPQRSTVWXZ][aeiouy]([bcdfghjklmnpqrstvwxz][aeiouy])+'        
    else:
        regex = r'[BCDFGHJKLMNPQRSTVWXZ][aeiouy]([bcdfghjklmnpqrstvwxz][aeiouy]){1,2} (([bcdfghjklmnpqrstvwxz][aeiouy]){1,3})+'
        
    #cycle to create the values       
    for i in range(0,table.fill_count):
        string = exrex.getone(regex)
        x = random.randint(2,max_range) #randomly generates varchar length for this iteration from range 
        
        fin = string[:x]                #cuts the obtained string
        values.append(fin)              #appends to the rest
        
     #TODO: check for white space at the end of string and delete it if yes
        
    return values
    
    
#returns array of bit values of the given length
def basic_bit(table, attr):
    
    if not attr.parameters :
        sys.stderr.write("Internal error. Parameter of attribute " + attr.name + " disappeared." \
                         "Recovery not possible, the functionality of Seeder is inconsistent from now on.\n")
        exit()
               
    values = []
    length = attr.parameters[0]
    regex = '[01]{' + str(length) + '}'
    
    for i in range(0,table.fill_count):
        fin = exrex.getone(regex)
        values.append(fin)              #appends to the rest 
    
    return values




#Char will be filled with random alfanumerical strings of given length
def basic_char(table, attr):
    
    if not attr.parameters :
        sys.stderr.write("Internal error. Parameter of attribute " + attr.name + " disappeared." \
                         "Recovery not possible, the functionality of Seeder is inconsistent from now on.\n")
        exit()
               
    values = []
    length = attr.parameters[0]
    
    regex = r'\w+'  
        
    #cycle to create the values       
    for i in range(0,table.fill_count):
        string = exrex.getone(regex)
        
        #if the generated string was too short
        while len(string)<length:
            string = string + exrex.getone(regex)
        
        fin = string[:length]           #cuts the obtained string
        values.append(fin)              #appends to the rest        
        
    return values
    
    

def basic_boolean(table, attr):
    
    values = []
    
    #cycle to create the values
    for i in range(0,table.fill_count):
        
        if (randint(0,9)%2) == 0:  #if random value is even -> True
            x = True
        else:
            x = False
        
        values.append(x)              #appends to the rest 
    
    return values




def basic_int(table, attr):
    
    values = []
    regex = r'[-]?\d+'
    
    #cycle to create the values
    for i in range(0,table.fill_count):
        
        num = exrex.getone(regex)        
        values.append(x)              #appends to the rest
        
    return values



#Basic fill function
#Recognizes the data type and uses it's basic method
def fm_basic(table, attr):
    
    values = []    # array for values
    
    
    #supported types for now: VARCHAR, BIT, CHAR, BOOLEAN, INT
    if attr.data_type == "VARCHAR":
        values = basic_varchar(table, attr)
        
    elif attr.data_type == "BIT":
        values = basic_bit(table, attr)
        
    elif attr.data_type == "CHAR":
        values = basic_char(table, attr)
        
    elif attr.data_type == "BOOLEAN":
        values = basic_bool(table, attr)
        
    elif attr.data_type == "INT":
        values = basic_int(table, attr)
        
    return values
