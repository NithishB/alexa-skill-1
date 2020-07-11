import re
import datefinder
import pickle as pkl
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
    deadline = {}

    for match in matches:
        num_dates.append(match)

    # TODO : Make this a bit more robust?
    if (len(num_dates)):
        deadline['deadline_date'] = num_dates[-1] # return the last occurrence as of now.
        # Also get the number of days remaining from today to that deadline.
        # A negative value of the remaining days means that the deadline has elapsed.
        deadline['num_days_remaining'] = (deadline['deadline_date'].date() - date.today()).days
        return deadline
    else:
        return None

if __name__=="__main__":

    # Define the search strings based on the data available.
    regexSearchStrings = [
        "by\s\w+day",
        "by\s\w+DAY",
        "no\slater\sthan\s\w+day",
        "no\slater\sthan\s\w+DAY"
    ]

    path = '/Users/adgdri/alexa-skill-1/alexa-skill-1/'
    fileName = 'mailObjectPickle_1.pkl'

    # Read in the pickle file that contains the extracted mails.
    mailOb = pkl.load(open(path+fileName,'rb'))

    # Iterate over the mail object, and extract the deadline dates, if any.
    for idx in range(len(mailOb)):
        print ('idx : ', idx)

        # Boolean variable to keep track of whether or not we might be having a possible deadline in the e-mail.
        deadlinePresence = False

        # Iterate over each regular expression string.
        for regexSearchString in regexSearchStrings:
            candidateMailLines = candidateStringSearchHelper(mailOb[idx]['body'], regexSearchString)

            # If candidateMailLines is empty, then we have no contenders for deadline date.
            if (candidateMailLines):
                # The result of this function call will be the deadline dates, if they are present, else None.
                deadlineDate = extractMailDate(candidateMailLines)
                if (deadlineDate):
                    deadlinePresence = True
                    print ( deadlineDate )
                break
        if (not deadlinePresence):
            print ('No deadline present.')
