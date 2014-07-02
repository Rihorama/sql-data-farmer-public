
import class_table
from method_basic import fm_basic
from method_regex import fm_regex
from method_textbank import fm_textbank, textbank_close
import sys
import random
from printer import errprint, ERRCODE


TABLE_DICT = {}  # dictionary of all tables (name:object)


#referenced type : referencing type(foreign key)
COMPATIBLE = {
    'BIGSERIAL': 'BIGINT',
    'SERIAL': 'INT',
    'BIGINT': 'BIGSERIAL',
    'INT': 'SERIAL',
    'INT': 'BIGSERIAL',
    'SERIAL': 'BIGINT',
}


#TODO: pripadne vyresit smazani seznamu promennych, kdyz uz nejsou treba
#checks if the given value has not been used to fill this attribute yet.
#returns True, if it's OK, False if it has been used
def check_unique(attr, value):

    #if the value belongs to a group that is supposed to be unique together
    #it's considered ok here so it passes
    if not attr.unique_group and value in attr.values_list:  # if
        return False

    return True


#checks if the given group of values has not been used in this table yet.
#returns True, if it's OK, False if it has been used
def check_unique_group(table, value):

    if value in table.unique_values:
        return False

    return True


#We remove last added value from every fk_pointed attribute.
#Same goes for single unique or primary key attributes
#Happens when we have to restart the last generated insert because
#group combination of some values in it is not unique.
def remove_last_saved(table):

    for attr in table.attr_list:
        if attr.fk_pointed or attr.unique_group == 0:
            attr.values_list.pop()


# Finds the value list for the attribute that the foreign key points to
# and randomly chooses and returns one value from it.
def get_foreign(attr):

    #special case of prefilled tables already in db
    #or the foreign key is filled by inserting DEFAULT
    if attr.fk_table.fill_count == "FILLED" or attr.fk_attribute.serial:
        value = "(select " + attr.fk_attribute.name + " from " + attr.fk_table.name \
                + " offset random() * (select count(*) from " + \
            attr.fk_table.name + ") limit 1)"
        return value

    if not attr.fk_assigned:  # we encounter this attr for the first time
        if (attr.unique or attr.primary_key) and not attr.unique_group:
            attr.fk_values = attr.fk_attribute.values_list[:]
                #duplicates the values list
        else:
            attr.fk_values = attr.fk_attribute.values_list  # only assigns the existing list

        attr.fk_assigned = True  # sets the flag - list of values has been set

    #gets list of the desired values to easily work with
    val_list = attr.fk_values

    length = len(val_list)
    #length_self = len(attr.values_list)    I have no idea where did this come from xD

    if length == 0:
        i = 0  # we have one item left (unique-fk combo issue only)
    else:
        i = random.randint(0, length-1)  # randomly chooses one index, minus 1 counts with empty endline

    #goes through only if not part of a group
    #I suppose the combo of single foreign key and group unique/pk is a bit wild but to make sure
    if (attr.unique or attr.primary_key) and not attr.unique_group:
        if len(val_list) != 0:  # we have something to take from
            value = val_list[i]
            del val_list[i]
                #removes the value so we can't use it again

        else:
            msg = "Input error: Unique foreign key attribute '" + attr.name + "' cannot be filled " \
                + "as the source attribute '" \
                + attr.fk_attribute.name + "' doesn't offer enough unique values.\n" \
                + "NOTE: Seeder can only work with values it's generating in this run - not with any others.\n"
            errprint(msg, ERRCODE["INPUT"])
    else:
        value = val_list[i]  # we don't care if it's repeated

    return value


###
#manages the array dimensions
def get_array(table, attr):

    #as stated in the docu, only BOX type uses semicolon as a delimiter character
    if attr.data_type == "BOX":
        delim = ";"
    else:
        delim = ","
    #---------------------------

    cnt = attr.array_dim_cnt
    val_list = []

    total = 1

    #for [x][y][z] we get value of x*y*z to know how many final values we want
    for x in attr.array_dim_size:
        total = total * x

    func = 'new_val = ' + attr.fill_method + '(table,attr)'

    #now we get the values and store them
    for i in range(0, total):
        try:
            exec func  # new_val = fill_method(attributes)
        except AttributeError:
            msg = "Internal error. Trouble using '" + attr.fill_method + "' method on attribute '" \
                + attr.name + "', table '" + table.name + "'.\n" \
                # + "NOTE: This may also be caused by a non existing method inserted.\n"
            errprint(msg, ERRCODE["INTERNAL"])

        if new_val[0] == "'" and new_val[-1] == "'":
            new_val = new_val[1:-1]  # cuts both the '
        new_val = "\"" + new_val + \
            "\""  # double quotes if the val contained commas or curly braces
        val_list.append(
            new_val)  # we append the newly received value to the list

    #now we'll put the array of cnt dimensions together (=the final value to fill the db with)
    old_list = val_list
    new_list = []

    #cycles dimension-times
    for i in range(0, cnt):
        j = cnt - (i+1)  # reverse the indexing so we go from back
        size = attr.array_dim_size[j]

        total = total / size  # we now have two separate numbers: 'total'-times we want field of 'size' values

        #cycles (the current dimension cnt - 1)-times
        for x in range(0, total):  # for [3][2][2] this happens 3*2 times, next cycle 3 times etc.
            new_val = "{"

            #cycles size-times of the currently last dimension
            for y in range(0, size):
                val = old_list.pop()
                new_val = new_val + val + delim

            new_val = new_val[:-1] + \
                "}"  # cut the last delimiter and ads the final '{'
            new_list.append(new_val)

        #now all old_list values should be used and in concatenated form stored in new_list
        #we replace old_list with new_list and create new new_list
        old_list = new_list
        new_list = []

    #once we finally get out off this ugly cycle chaos, old_list should contain one item
    #made of all previous items etc.
    new_val = "'" + old_list.pop() + "'"

    return new_val


# Returns a string concatenated of generated values for each attribute
def get_values(table):

    unique_values = []
        #to store all values that create a unique/pk group
    values = ""

    for attr in table.attr_list:

        new_val = None

        if attr.foreign_key:  # foreign key is filled from existing values
            new_val = get_foreign(attr)

        elif attr.serial:
            new_val = "DEFAULT"  # next sequence

        elif attr.array_flag:  # array needs a special treatment
            new_val = get_array(table, attr)

        else:
            func = 'new_val = ' + attr.fill_method + '(table,attr)'

            try:
                exec func  # new_val = fill_method(attributes)
            except AttributeError:
                msg = "Internal error. Trouble using '" + attr.fill_method + "' method on attribute '" \
                      + attr.name + "', table '" + table.name + "'.\n"
                      #+ "NOTE: This may also be caused by a non existing method inserted.\n"
                errprint(msg, ERRCODE["INTERNAL"])

        #these combinations are filled with embedded SELECT query so no checking for them
        test0 = attr.unique and attr.foreign_key and not attr.fk_attribute.serial
        test1 = attr.unique and attr.foreign_key and not attr.fk_table.fill_count == "FILLED"

        #serial is unique by its sequence, if it overflows because of low capacity, it's user's problem
        test2 = attr.unique and not attr.serial
        test3 = attr.primary_key and not attr.serial

        #if one test true, we must ensure the inserted value hasn't been used yet
        if test0 or test1 or test2 or test3:
            timeout = 0
            while not check_unique(attr, new_val):  # validity check if there is unique/primary key constraint
                if timeout >= 100:
                    msg = "Runtime error: The timeout for finding new unique value for attribute '" + attr.name + "' exceeded.\n" \
                          "Tip: Check if the given fill method offers enough unique values.\n"
                    errprint(msg, ERRCODE["RUNTIME"])

                if attr.foreign_key:
                    new_val = get_foreign(attr)
                else:
                    exec func  # we call the method again (and again)

                timeout += 1

        #DEFAULT appearance chance
        if attr.default:
            chance = random.randint(0, 100)
            if chance < attr.default_value:
                new_val = 'DEFAULT'

        #NULL appearance chance
        if attr.null:
            chance = random.randint(0, 100)
            if chance < attr.constraint_parameters:
                new_val = 'NULL'

        values = values + str(new_val) + ", "  # concatenates the new value with the rest and divides with a ','

        if attr.fk_pointed or attr.unique or attr.primary_key:  # we will need these values either for filling foreign key attributes

            if attr.unique_group and not attr.fk_pointed:  # this value has meaning only in group
                unique_values.append(new_val)
            elif attr.unique_group and attr.fk_pointed:  # value important alone and in group as well
                attr.values_list.append(new_val)
                unique_values.append(new_val)
            else:
                attr.values_list.append(
                    new_val)  # value important alone

    values = values[:-2]
        #removes the ',' from the end of the string once we end

    return {'values': values, 'unique_values': unique_values}


#checks if the table foreign keys point only to already filled tables
#if yes, adds the table to the FILLABLE_LIST and returns True, else False
def table_check(table):

    flag = True  # all ok so far

    for attr in table.attr_list:
        if attr.foreign_key:
            if not attr.fk_table.solved:  # this attribute can't be filled as the foreign table hasn't been solved yet
                flag = False  # problem found
                break

    return flag


#takes the table and creates an insert string
def table_filler(table):

    if not table_check(table):  # checks if we know enough to fill this table
        return True  # means there is an unifnished table

    for i in range(0, table.fill_count):
        flag = True

        timeout = 0
        while flag and timeout < 100:
            flag = False
            result = get_values(table)
            values = result['values']
            unique_values = result['unique_values']

            if len(unique_values) > 0 and not check_unique_group(table, unique_values):
                flag = True  # this set of values has already been used, we need to do it all again
                remove_last_saved(table)  # will remove all values possibly saved during this generating
                timeout += 1

            elif len(unique_values) > 0:  # group is unique as checked in above branch
                table.unique_values.append(unique_values)  # we append so this combo cannot be used again

        if timeout >= 100:
            msg = "Runtime error: The timeout for finding new unique value combination for table '" + table.name + "' exceeded.\n" \
                  "Tip: Check if the given fill method offers enough unique combinations.\n"
            errprint(msg, ERRCODE["RUNTIME"])

        string = "INSERT INTO " + table.name + "\n" + "VALUES (" + \
            values + ");\n"
        print string
        textbank_close(table)  # closes the file if it's opened

    table.solved = True
    return False  # no problems with this table


#main filling loop for all tables
def db_filler(table_list):

    iniciate_fk(table_list)  # calls the iniciatiation

    i = True
    while i:
        i = False  # changed to true if a table is left unfilled

        for table in table_list:
            if table.solved == False:  # this table hasn't been filled yet
                y = table_filler(table)
                i = y or i  # if one is true, it remains true and we can't stop yet


  #TODO: make some kind of timeout with a message if it exceedes
##
#INICIALIZATION
##
#makes a dictionary table_name:object
#
def create_table_dict(table_list):

    global TABLE_DICT

    for table in table_list:

        if table.name in TABLE_DICT:
            msg = "Semantic error: Duplicate in table names found!\n"
            errprint(msg, ERRCODE["SEMANTIC"])

        TABLE_DICT[table.name] = table


#for every attribute that is a FK iniciates its variables fk_table and fk_attribute
#with the correct objects using TABLE_DICT
#till this function there are only string names in these variables
def iniciate_fk(table_list):

    global TABLE_DICT
    create_table_dict(table_list)

    for table in table_list:

        if table.fill_count == "FILLED":  # this table is prefilled in the database
            table.solved = True  # so we are not filling it here

        if table.fk:  # if this table contains foreign keys

            for attr in table.attr_list:  # we cycle over its attributes

                #first compatibility-of-constraints check
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

                #and the main part, getting the foreign key dependences done
                if attr.foreign_key:

                    ftable_name = attr.fk_table  # stores the name of the foreign table and its attribute
                    fattr_name = attr.fk_attribute

                    #checks if this table actually exists in our dictionary
                    if ftable_name in TABLE_DICT:
                        ftable = TABLE_DICT[
                            ftable_name]  # foreign table object
                    else:
                        msg = "Input error: The given foreign table '" + \
                            ftable_name + "' doesn't exist."
                        errprint(msg, ERRCODE["INPUT"])

                    #we know the table exists, now let's try to find the attribute
                    fattr = None
                    for f_attribute in ftable.attr_list:
                        if f_attribute.name == fattr_name:  # this is the attribute foreign key points to
                            fattr = f_attribute  # foreign attribute object
                            break

                    if fattr is None:
                        msg = "Semantic error: The given foreign attribute '" + fattr_name + "' doesn't exist in table '" \
                            + ftable_name + "'."
                        errprint(msg, ERRCODE["SEMANTIC"])

                    #types not compatible

                    #print "FATTR", fattr.data_type, "ATTR", attr.data_type
                    #print "FATTR KEY ->",COMPATIBLE[fattr.data_type]

                    if fattr.data_type != attr.data_type and COMPATIBLE[fattr.data_type] != attr.data_type:
                        msg = "Semantic error: The foreign-key-type attribute '" + attr.name + "'s data type doesn't correspond with " \
                              "the data type of the attribute it references to. Table: '" + table.name + "'\n"
                        errprint(msg, ERRCODE["SEMANTIC"])

                    #data types might be the same but if one is array and other is not, it would mean trouble
                    elif fattr.data_type == attr.data_type and not (fattr.array_flag == attr.array_flag):
                        msg = "Semantic error: The foreign-key-type attribute '" + attr.name + "'s data type doesn't correspond with " \
                              "the data type of the attribute it references to. One is array, one is not. Table: '" + table.name + "'\n"
                        errprint(msg, ERRCODE["SEMANTIC"])

                    #let's check that array of arrays of arrays doesn't refer to only an array
                    elif fattr.data_type == attr.data_type and fattr.array_flag and attr.array_flag:
                        if fattr.array_dim_cnt != attr.array_dim_cnt:
                            msg = "Semantic error: The foreign-key-type attribute '" + attr.name + "' has a different count of " \
                                  + "dimensions than the array attribute it references to. Table: '" + table.name + "'\n"
                            errprint(msg, ERRCODE["SEMANTIC"])

                    #NOTE: As stated in postgresql docu, all arrays are now behaving as infinite,
                    #      max size given or not. So for now there is no reason to check compatibility
                    #      of individual array sizes. May change.
                    #now we have both objects, we can store them in the variables
                    attr.fk_table = ftable
                    attr.fk_attribute = fattr
                    attr.fk_attribute.fk_pointed = True
                    attr.fk_attribute.fk_times += 1  # increments count of "how many points at me"
