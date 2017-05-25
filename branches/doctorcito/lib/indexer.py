#!/usr/bin/python
### import modules
import subprocess
import sys
import os
import string

### define classes

# Indexer object
# holds a list of patterns to search for and has
# a method to actually do the searching.
# List of applicable patterns is to be filled with Indexer.addPattern(pattern="").
# When Indexer.run(text="") is called, it expects a string in which it searches for each pattern.
# The string is split into a list of words by applying text.split(" "). The string containig the text
# to be searched must be cleaned from any non-printable characters a.s.o (for excample carriage return)
# by your main programm. You also need to strip out any surplus blanks.
class Indexer:
    # constants
    # Mode constants for parser
    # these should probably be private and i'm thinking about a way to
    # do this without loosing the comfort of comprehensive naming
    WORDS = 1
    LINES = 2

    # some initialisations
    # pattern list
    __patterns = []
    # result dictionary, actually will be a nested dictionary
    __results = {}
    # text list
    __text = []
    # active pattern dictionary
    __active_pattern = {}


    # addPattern Method to add a nested pattern dictionary to the list of patterns
    # takes the pattern as mandatory, mode (defaults to WORDS)
    # and count (defaults to 1) as parameters
    def addPattern(self, pattern, mode=WORDS, count=1):
        self.__patterns.append({'pattern': pattern, 'mode': mode, 'count': count})


    # __run_lines Method for LINES mode
    # Searches for 'pattern' in each line of text and returns 'count' lines
    # as result in a result list.
    def __run_lines(self):
        resultbuffer = []
        for line in self.__text:
            if line.find(self.__active_pattern['pattern']) >= 0:
                start = self.__text.index(line) + 1
        if self.__text[start:start + self.__active_pattern['count']] not in resultbuffer:
            for buff in (self.__text[start:start + self.__active_pattern['count']]):
                resultbuffer.append(buff.strip())
        self.__results[self.__active_pattern['pattern']] = resultbuffer


    # __run_words for WORDS mode
    # Searches for 'patten' in text word by word and returns 'count' words
    # as a result list
    def __run_words(self):
        # put lines together to a single string that then can be split into words
        text = ""
        for line in self.__text:
            text = text + line

        # replace carriage returns with blanks to make string splittable by blanks
        # and keep it reliably searchable
        text = string.replace(text, "\n"," ")

        # split text string into a list of words by blanks
        wordlist = text.split(" ")

        # get the search pattern from __active_pattern
        # this is a tribute to the old version of this function and
        # can be changed some time...
        pattern = self.__active_pattern['pattern']

        # initialise a buffer to hold results for this pattern in a list
        resultbuffer = []

        # set findings counter to 0, we will stop searching for 'pattern'
        # once we found all appearances.
        count = 0

        # start index set to 0 to start at beginning of wordlist
        start = 0

        # search in wordlist for pattern until all where found,
        # no point in searching to the end when all found
        while count < wordlist.count(pattern):
            # get the index of next appearance of 'pattern' in the list
            # starting at 'start' index point
            found = wordlist.index(pattern,start)

            # raise start index for next run by one to get to the next list element
            start = found + 1

            # raise find counter by one
            # hell... i dont know if this is still needed...
            count = count + 1

            # set the temporary result string to empty string
            resstring = ""

            # take a slice of wordlist containing 'count' words after
            # pattern position and construct a string containing those
            # words seperated by blank.
            for buff in wordlist[start:start + self.__active_pattern['count']]:
                resstring = resstring + " " + buff

            # strip the resulting string from unprintable characters
            resstring = resstring.strip()

            # put resulting string to the resultbuffer list, if it is not
            # already in it, we don't want duplicates.
            if not resstring in resultbuffer:
                try:
                    resultbuffer.append(resstring)
                except:
                    print "error in resultbuffer"

        # Finally append the resultbuffer list to Indexers result dictionary
        self.__results[pattern] = resultbuffer


    # The run method calling the private parser methods sequentially
    # for each pattern.
    def run(self,text=[]):
        self.__text = text
        for pat in self.__patterns:
            self.__active_pattern = pat
# This is for debugging only
#            print pat
# end debug
            # create parser function dictionary, need to do this here, no way to use self outside of
            # object method. and no way to use __run_* without self
            # I even need to define this here, because python throws an exception, that there is no self.__active_pattern
            # when this is defined outside loop
            functions = {1: self.__run_words, 2: self.__run_lines}
            functions[self.__active_pattern['mode']]()
        return self.__results


