import argparse
from subprocess import Popen, PIPE
import os
import re
import csv
import dateutil.parser
import datetime


def reparse_date(date_string, year):
    """date_string was originally year-less, so make it explicit"""
    d = datetime.datetime.strptime(date_string, "%m/%d")

    if not year:
        raise Exception("Year not specified")
    elif isinstance(year, tuple):
        # each statement only covers one month
        if d.month == 12:
            d = datetime.datetime(year[0], d.month, d.day)
        elif d.month == 1:
            d = datetime.datetime(year[1], d.month, d.day)
        else:
            raise Exception("Month not December or January and year is a range")
    else:
        d = datetime.datetime(year, d.month, d.day)

    return d.strftime("%m/%d/%Y")

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

    def parse_line(self, line, state):
        pass

class DepositParser(Parser):
    def __init__(self, filename):
        Parser.__init__(self, filename, ".deposit.csv")

    def is_header(self, line):
        return line.startswith("DEPOSITS & OTHER CREDITS")

    def parse_line(self, line, state):
        if re.match("^(\d\d/\d\d\ )", line):
            columns = line.split(" ")
            columns = [column.strip() for column in columns if column.strip()]
            if len(columns) >= 3:
                columns = [columns[0], " ".join(columns[1:-1]), columns[-1]]
                # add year to date
                columns[0] = reparse_date(columns[0], state.year)
                # remove thousands comma
                columns[-1] = columns[-1].replace(",", "")
            else:
                raise Exception("Weird number of columns: %s" % line)

            self.writer.writerow(columns)

class CheckParser(Parser):
    def __init__(self, filename):
        Parser.__init__(self, filename, ".check.csv")

    def is_header(self, line):
        return line.startswith("CHECKS PAID")

    def parse_line(self, line, state):
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

    def parse_line(self, line, state):
        if re.match("^(\d\d/\d\d\ )", line):
            columns = line.split(" ")
            columns = [column.strip() for column in columns if column.strip()]
            if len(columns) >= 3:
                columns = [columns[0], " ".join(columns[1:-1]), columns[-1]]
                # add year to date
                columns[0] = reparse_date(columns[0], state.year)
                # remove thousands comma
                columns[-1] = columns[-1].replace(",", "")
                    
            else:
                raise Exception("Weird number of columns: %s" % line)
            self.writer.writerow(columns)

class DateParser(Parser):
    def __init__(self, filename):
        Parser.__init__(self, filename, ".date.csv")

    def is_header(self, line):
        return line.strip().startswith("Statement Date ")

    def parse_line(self, line, state):
        if " Through " in line:
            s1, s2 = line.split(" Through ")
            d1 = dateutil.parser.parse(s1.strip())
            year_string = re.search("\d\d\d\d", s2).group(0)
            index = s2.index(year_string)
            if index < 0:
                raise Exception("Index less than 0")
            d2 = dateutil.parser.parse(s2[:index + len(year_string)])

            if d1.year != d2.year:
                state.year = (d1.year, d2.year)
            else:
                state.year = d1.year
        
class BalanceParser(Parser):
    def __init__(self, filename):
        Parser.__init__(self, filename, ".balance.csv")

    def is_header(self, line):
        return line.startswith("BALANCE SUMMARY")

    def parse_line(self, line, state):
        # this exists to prevent DepositParser or WithdrawalParser from using this information wrongly
        pass

class State:
    """Holds information to pass between parsers"""
    def __init__(self):
        self.year = None

class Pdf2Csv:
    
    def __init__(self, filename):
        if not os.path.isfile(filename):
            raise Exception("%s must be a pdf file" % filename)
        self.parsers = [DefaultParser(filename),
                        BalanceParser(filename),
                        CheckParser(filename),
                        WithdrawalParser(filename),
                        DepositParser(filename),
                        DateParser(filename)]
        self.filename = filename


        self.current_parser = self.parsers[0]
        self.state = State()

        

    def pdf_to_csv(self):
        output = Popen(["pdftotext", "-layout", self.filename, "-"], stdout=PIPE).communicate()[0]

        for line in output.split("\n"):
            line = line.strip()
            for parser in self.parsers:
                if parser.is_header(line):
                    self.current_parser = parser
                    break
            else:
                self.current_parser.parse_line(line, self.state)

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
