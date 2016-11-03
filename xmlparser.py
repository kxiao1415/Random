#!/usr/bin/env python

import re, os
import argparse
from HTMLParser import HTMLParser


TRANSLATIONS = {"\xc5\xbf": "s",
                "\xc5\x93": "oe",
                "\xc5\x8e": "o",
                "\xc3\x86": "Ae",
                "\xc3\xa6": "ae",
                "\xc3\xa9": "e",
                "\xc3\xb1": "n",
                "\xc3\xb3": "o",
                "\xc3\xb4": "o",
                "\xc4\x93": "e",
                "\xc3\xa3": "a",
                "\xc3\xa7": "c",
                "\xc3\xb5": "o",
                "\xc3\xba": "u",
                "\xc3\xa9": "e",
                "\xc3\xa1": "a"}

def excludeSection(data,section):
    """
    return a text block (data) with a specific portion subbed out (bounded by <SECTION>)
    """
    data = re.compile('<{0}.*</{0}>'.format(section), re.DOTALL).sub('',data)

    return data


def cleanUpMatch(match):
    # remove everything between double line breaks
    match = re.sub(r'\n\s*\n.*?\n\s*\n', '', match, flags=re.DOTALL)

    # remove soft hyphen
    match = re.sub(r'&#xAD;(\n)*(<lb/>)*', '', match)
    
    # remove box character
    match = re.sub(r'\xc2\xad(\n)*(<lb/>)*', '', match)
    
    # replace <lb/> or '\n' with ' '
    match = re.sub(r'<lb/>|\n', ' ', match)

    # remove everything between '<>'
    match = re.sub(r'<.*?>', '', match)
    
    # translate special characters
    for char in TRANSLATIONS:
        match = match.replace(char, TRANSLATIONS[char])
    
    # remove extra white spaces
    match = ' '.join(match.split())
    
    # decode html characters
    match = HTMLParser().unescape(match)

    # always normalize to lower case
    return match.lower()


def simplifyDict(dict):

    pass

    return dict


def getAllFilesToProcess(files, directory):
    files_to_process = []
    
    if files:
        files_to_process += files
    
    if directory:
        for root, directories, file_names in os.walk(directory):
            for file_name in file_names:
                 files_to_process.append(os.path.join(root,file_name))
                
    return files_to_process


def extractAuthorWork(file):
    (author, work, fileType) = file.split('.')

    return author, work, fileType


def getDate(file):
    with open(file, 'r') as f:
        data = f.read()

        # extract '<title type = "main"...</title>' block
        title = re.compile('<title type="main".*?</title>', re.DOTALL).findall(data)

        # run cleanUp to clean formatting so raw content only
        title = cleanUpMatch(title[0])

        # last 4 characters SHOULD always be date
        date = title[-4:]

        return date


def exportData(dict, metadata=[]):

    if metadata:
        for match in dict:
            outLine = '\t'.join(metadata) + "\t" + match + "\t" + str(dict[match])

            print outLine
    else:
        for match in dict:
            outLine = '\t'.join(metadata) + "\t" + match + "\t" + str(dict[match])

            print outLine


def xmlParser(file, tag):
    '''
    Restructured so this only parses, doesn't return.
    Removed the "print cleanMatch" since now that is exportData's job
    Hence, this now returns dict, which exportData then takes, with any associated metadata, and prints all at you
    '''

    dict = {}

    with open(file, 'r') as f:
        data = f.read()

        # exclude specific sections teiHeader, front, back
        for section in ['teiHeader', 'front', 'back']:
            data = excludeSection(data=data, section=section)
        
        pattern = '<{0}.*?>(.*?)</{1}>'.format(tag, tag)
        for match in re.compile(pattern, re.DOTALL).finditer(data):
            cleanMatch = cleanUpMatch(match.group())
            if cleanMatch in dict:
                dict[cleanMatch] += 1
            else:
                dict[cleanMatch] = 1

        # run simplifyDict to try to combine easily detectable overlaps like 'lex ington' vs 'lexington'
        dict = simplifyDict(dict)

        return dict



if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='xml parser to Samuel')
    parser.add_argument('-f', action='store', dest='files', default=[], nargs='+', help='Add files to a list')
    parser.add_argument('-d', action='store', dest='directory', help='This will process all files in the directory')
    parser.add_argument('-t', action='store', dest='tag', help='xml tag', required=True)
    parser.add_argument('--version', action='version', version='%(prog)s 1.0')
    args = parser.parse_args()

    # requires at least '-f' or '-d' is required
    if not (args.files or args.directory):
        parser.error("At least a '-f' or a '-d' is required")

    files = getAllFilesToProcess(args.files, args.directory)

    for file in files:
        # parse out & count tags into a dict
        counts = xmlParser(file, args.tag)

        # get author, work from that filename
        author, work = extractAuthorWork(file)[0:2]

        # get date from the file
        date = getDate(file)

        # export counts
        exportData(counts, metadata=[author, work, date])


