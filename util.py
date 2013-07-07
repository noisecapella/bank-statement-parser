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

