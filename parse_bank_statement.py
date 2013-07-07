import argparse
from subprocess import Popen, PIPE
import os
import re
import csv
import dateutil.parser
import datetime
from util import reparse_date
from parsers import DefaultParser, Parser, State, Pdf2Csv

class DepositParser(Parser):
    def __init__(self, filename):
        Parser.__init__(self, filename, ".deposit.csv")

    def is_header(self, line, state):
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

    def is_header(self, line, state):
        return line.startswith("CHECKS PAID")

    def parse_line(self, line, state):
        if re.match("^\d\d\d\d\d\d\ ", line):
            columns = line.split(" ")
            columns = [column.strip() for column in columns if column.strip()]
            if len(columns) == 0:
                raise Exception("Weird number of columns: %s" % line)
            if len(columns) % 3 == 0:
                for i in xrange(len(columns) / 3):

                    check_num, check_date, check_amount = columns[i*3:(i+1)*3]
                    check_date = reparse_date(check_date, state.year)
                    check_amount = check_amount.replace(",", "")
                    self.writer.writerow([check_num, check_date, check_amount])
        

class WithdrawalParser(Parser):
    def __init__(self, filename):
        Parser.__init__(self, filename, ".withdrawal.csv")

    def is_header(self, line, state):
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

    def is_header(self, line, state):
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

    def is_header(self, line, state):
        return line.startswith("BALANCE SUMMARY")

    def parse_line(self, line, state):
        # this exists to prevent DepositParser or WithdrawalParser from using this information wrongly
        pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("filename")
    args = parser.parse_args()

    parser_classes = [DefaultParser, 
                      BalanceParser,
                      CheckParser,
                      WithdrawalParser,
                      DepositParser,
                      DateParser]
    p = Pdf2Csv(args.filename, parser_classes)
    p.pdf_to_csv()
    p.close()
    
    
if __name__ == "__main__":
    main()
