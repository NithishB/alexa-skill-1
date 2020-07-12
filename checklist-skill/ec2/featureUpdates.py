import re
import datefinder
from datetime import date


def candidateStringSearchHelper(mailBody , regexSearchString):
    '''
        * Helper function that will help us pinpoint only those lines that we need to consider for extracting the
        date. (uses regular expressions)
        * Pass only the body of a single e-mail to this function at a time.
        Input:
            body : (String) String that contains the body of the e-mail that we're parsing the date for.
            idx  : (int) The index position of the string in the list of sentences in the body of the mail.
            regexSearchString : (String) This is the regular expression that will aid us in narrowing down the
                                target sentence.
        Output:
            A string that is the most likely component in the body of the e-mail to contain the due-date.
        Dependency:
            import re
    '''

    candidateMailLines = []
    NULL_STR = ''

    for splitString in mailBody.split('.'):
        # More generic search string. If the length of the matches associated with this search string is greater
        # than 1, then we'll go in for a more streamlined search.
        x = re.findall(regexSearchString, splitString)
        if (len(x) == 1):
            candidateMailLines.append(splitString)

    if (len(candidateMailLines) == 1):
        return candidateMailLines[0]
    else:
        return NULL_STR


def extractMailDate(mailBody=''):
    '''
        Function that takes in a string as input, and searches for the occurrence of a date within that input,
        and returns it, if no such date is present, then it returns None
        Input:
            body : (String) The contents of the e-mail as a string.
        Output:
            date : DateTime object ( (Year, Month, Day, Hour, Minutes) )
        Dependencies:
            This function depends on the python package : datefinder.
            You can install it using pip : pip install datefinder
    '''
    num_dates = []
    matches = datefinder.find_dates(mailBody)
    deadline = {'date': "", 'days': ""}

    for match in matches:
        num_dates.append(match)

    # TODO : Make this a bit more robust?
    if len(num_dates):
        try:
            deadline['date'] = num_dates[-1].date()  # return the last occurrence as of now.
            deadline['days'] = (deadline['date'] - date.today()).days
            return deadline
        except:
            return deadline
    else:
        return deadline


def get_mail_end_date(body):
    regexSearchStrings = [
        "by\s\w+day",
        "by\s\w+DAY",
        "no\slater\sthan\s\w+day",
        "no\slater\sthan\s\w+DAY"
    ]

    # Iterate over each regular expression string.
    for regexSearchString in regexSearchStrings:
        candidateMailLines = candidateStringSearchHelper(body, regexSearchString)

        # If candidateMailLines is empty, then we have no contenders for deadline date.
        if (candidateMailLines):
            # The result of this function call will be the deadline dates, if they are present, else None.
            return extractMailDate(candidateMailLines)

    return {'date': "", 'days': ""}
