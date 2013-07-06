import argparse
from subprocess import Popen, PIPE
import os
import re
import csv

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

    def is_header(self, line):
        return False

    def parse_line(self, line):
        pass

class DepositParser(Parser):
    def __init__(self, filename):
        Parser.__init__(self, filename, ".deposit.csv")

    def is_header(self, line):
        return line.startswith("DEPOSITS & OTHER CREDITS")

    def parse_line(self, line):
        if re.match("^(\d\d/\d\d\ )", line):
            columns = line.split(" ")
            columns = [column.strip() for column in columns if column.strip()]
            if len(columns) >= 3:
                columns = [columns[0], " ".join(columns[1:-1]), columns[-1]]
            else:
                raise Exception("Weird number of columns: %s" % line)

            self.writer.writerow(columns)

class CheckParser(Parser):
    def __init__(self, filename):
        Parser.__init__(self, filename, ".check.csv")

    def is_header(self, line):
        return line.startswith("CHECKS PAID")

    def parse_line(self, line):
        if re.match("^\d\d\d\d\d\d\ ", line):
            columns = line.split(" ")
            columns = [column.strip() for column in columns if column.strip()]
            if len(columns) == 0:
                raise Exception("Weird number of columns: %s" % line)
            if len(columns) % 3 == 0:
                for i in xrange(len(columns) / 3):
                    self.writer.writerow(columns[i*3:(i+1)*3])
        

class WithdrawalParser(Parser):
    def __init__(self, filename):
        Parser.__init__(self, filename, ".withdrawal.csv")

    def is_header(self, line):
        return line.startswith("WITHDRAWALS & OTHER DEBITS")

    def parse_line(self, line):
        if re.match("^(\d\d/\d\d\ )", line):
            columns = line.split(" ")
            columns = [column.strip() for column in columns if column.strip()]
            if len(columns) >= 3:
                columns = [columns[0], " ".join(columns[1:-1]), columns[-1]]
            else:
                raise Exception("Weird number of columns: %s" % line)
            self.writer.writerow(columns)
            

class BalanceParser(Parser):
    def __init__(self, filename):
        Parser.__init__(self, filename, ".balance.csv")

    def is_header(self, line):
        return line.startswith("BALANCE SUMMARY")

    def parse_line(self, line):
        # this exists to prevent DepositParser or WithdrawalParser from using this information wrongly
        pass

class Pdf2Csv:
    
    def __init__(self, filename):
        if not os.path.isfile(filename):
            raise Exception("%s must be a pdf file" % filename)
        self.parsers = [DefaultParser(filename),
                        BalanceParser(filename),
                        CheckParser(filename),
                        WithdrawalParser(filename),
                        DepositParser(filename)]
        self.filename = filename


        self.state = self.parsers[0]

        

    def pdf_to_csv(self):
        output = Popen(["pdftotext", "-layout", self.filename, "-"], stdout=PIPE).communicate()[0]

        for line in output.split("\n"):
            line = line.strip()
            for parser in self.parsers:
                if parser.is_header(line):
                    self.state = parser
                    break
            else:
                self.state.parse_line(line)

    def close(self):
        for parser in self.parsers:
            parser.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("filename")
    args = parser.parse_args()

    p = Pdf2Csv(args.filename)
    p.pdf_to_csv()
    p.close()
    
    
if __name__ == "__main__":
    main()
