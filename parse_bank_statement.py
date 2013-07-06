import argparse
from subprocess import Popen, PIPE
import os

class Parser:
    def __init__(self, filename, extension):
        if not os.path.isfile(filename):
            raise Exception("%s must be a pdf file" % filename)

        self.f = open(filename + extension, "wb")
        
    def close(self):
        self.f.close()

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
        pass

class CheckParser(Parser):
    def __init__(self, filename):
        Parser.__init__(self, filename, ".check.csv")

    def is_header(self, line):
        return line.startswith("CHECKS PAID")

    def parse_line(self, line):
        pass

class WithdrawalParser(Parser):
    def __init__(self, filename):
        Parser.__init__(self, filename, ".withdrawal.csv")

    def is_header(self, line):
        return line.startswith("WITHDRAWALS & OTHER DEBITS")

    def parse_line(self, line):
        pass

class BalanceParser(Parser):
    def __init__(self, filename):
        Parser.__init__(self, filename, ".balance.csv")

    def is_header(self, line):
        return line.startswith("BALANCE SUMMARY")

    def parse_line(self, line):
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

        for line in output:
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
