import datefinder

def extractMailDate(body = ''):
    '''
        Function that takes in a string as input, and searches for nthe occurrence of a date within that input,
        and returns it, if no such date is present, then it returns None
        
        Input:
            body : String
        
        Output:
            date : DateTime object ( (Year, Month, Day, Hour, Minutes) )
            
        Dependencies:
            This function depends on the python package : datefinder.
            You can install it using pip : pip install datefinder
    '''
    num_dates = []
    # NOTE : import datefinder.
    matches = datefinder.find_dates(body)
    
    for match in matches:
        num_dates.append( match )
        
    # TODO : Make this more robust?
    if ( len(num_dates) ):
        return num_dates[0] # return the first occurrence as of now.
    else:
        return None



