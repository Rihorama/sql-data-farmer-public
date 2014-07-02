
import class_table
import exrex
import random
import sys

#

#User-controlled fill function
#Uses the given regex and returns a correct string
#Now accepting CHAR, VARCHAR, TEXT and INT (SMALLINT and BIGINT as well)


def fm_regex(table, attr):

    regex = attr.fill_parameters[0]
    regex = regex[1:-1]  # cuts the quotes

    value = exrex.getone(regex)

    #NOTE: If the given regex allows shorter results than the given length,
    #      the final result will be created by adding empty space by db.
    #      On contrary - if the given regex produced longer result, it will be cut
    if attr.data_type == "CHAR":
        length = attr.parameters[0]

        while len(value) < length:
            value = value + exrex.getone(regex)
        value = value[:length]

    elif attr.data_type == "VARCHAR":
        length = attr.parameters[0]
        value = value[:length]

    quoted = (
        'VARCHAR', 'CHAR', 'TEXT', 'BIT', 'BOX', 'CIDR', 'CIRCLE', 'DATE', 'INET',
        'LSEG', 'PATH', 'POINT', 'POLYGON', 'TIME', 'TIMESTAMP')

    #if the type has to be inserted in quotes, they are added
    if attr.data_type in quoted:
        value = "'" + str(value) + "'"

    #if the data type requires to be inserted with a prefix like: bit'100110', it's added here
    elif attr.data_type == 'BIT':
        value = 'bit' + value
    elif attr.data_type == 'BOX':
        value = 'box' + value
    elif attr.data_type == 'CIDR':
        value = 'cidr' + value
    elif attr.data_type == 'CIRCLE':
        value = 'circle' + value
    elif attr.data_type == 'INET':
        value = 'lseg' + value
    elif attr.data_type == 'PATH':
        value = 'path' + value
    elif attr.data_type == 'POINT':
        value = 'point' + value
    elif attr.data_type == 'POLYGON':
        value = 'polygon' + value

    return value
