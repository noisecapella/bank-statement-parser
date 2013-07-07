import argparse
from subprocess import Popen, PIPE
import os
import re
import csv
import dateutil.parser
import datetime
from util import reparse_date
from parsers import Parser, DefaultParser, State, Pdf2Csv

class DateParser(Parser):
    def __init__(self, filename):
        Parser.__init__(self, filename, ".date.csv")

    def is_header(self, line, state):
        to_match = "Statement Closing Date "
        if line.strip().startswith(to_match):
            date_string = line.strip()[len(to_match):].strip()
            date = dateutil.parser.parse(date_string)

            if date.month == 1:
                state.year = (date.year - 1, date.year)
            else:
                state.year = date.year
        return False

    def parse_line(self, line, state):
        pass
        
class TransactionParser(Parser):
    def __init__(self, filename):
        Parser.__init__(self, filename, ".transaction.csv")

    def is_header(self, line, state):
        return line.startswith("TRANSACTIONS")

    def parse_line(self, line, state):
        if re.match("^[A-Z0-9]{17}", line):
            columns = line.split(" ")
            columns = [column.strip() for column in columns if column.strip()]
            date_string = columns[1]
            date_string = reparse_date(date_string, state.year)
            description = " ".join(columns[3:-1])
            price = columns[-1]
            price = price.strip().replace(",", "")
            if price.endswith("-"):
                withdrawal = price[:-1]
                deposit = ""
            else:
                deposit = price
                withdrawal = ""
            self.writer.writerow([date_string, description, deposit, withdrawal])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("filename")
    args = parser.parse_args()

    p = Pdf2Csv(args.filename, [DefaultParser,
                                TransactionParser,
                                DateParser])
    p.pdf_to_csv()
    p.close()
    
    
if __name__ == "__main__":
    main()
