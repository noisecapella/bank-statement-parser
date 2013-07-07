import os
import csv
from subprocess import Popen, PIPE

class Parser:
    def __init__(self, filename, extension):
        if not os.path.isfile(filename):
            raise Exception("%s must be a pdf file" % filename)

        self._f = open(filename + extension, "wb")
        self.writer = csv.writer(self._f)
        
    def close(self):
        self._f.close()
class DefaultParser(Parser):
    """Dummy parser which is active at the beginning until something else becomes active"""
    def __init__(self, filename):
        Parser.__init__(self, filename, ".default.csv")

    def is_header(self, line, state):
        return False

    def parse_line(self, line, state):
        pass



class State:
    """Holds information to pass between parsers"""
    def __init__(self):
        self.year = None

class Pdf2Csv:
    
    def __init__(self, filename, parser_classes):
        if not os.path.isfile(filename):
            raise Exception("%s must be a pdf file" % filename)
        self.parsers = [parser(filename) for parser in parser_classes]
        
        self.filename = filename


        self.current_parser = self.parsers[0]
        self.state = State()

        

    def pdf_to_csv(self):
        output = Popen(["pdftotext", "-layout", self.filename, "-"], stdout=PIPE).communicate()[0]

        for line in output.split("\n"):
            line = line.strip()
            for parser in self.parsers:
                if parser.is_header(line, self.state):
                    self.current_parser = parser
                    break
            else:
                self.current_parser.parse_line(line, self.state)

    def close(self):
        for parser in self.parsers:
            parser.close()

