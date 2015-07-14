import re
import sys
import csv
import argparse
import StringIO
import requests
from datetime import datetime, timedelta

BASE_URL = 'http://www.eia.gov/petroleum/supply/weekly/archive/%s/csv/table4.csv'


class OilInventory(object):
    def __init__(self, num_weeks=1):
        self.num_weeks = num_weeks
        self.inventories = []

    def get_report_days(self):
        now = datetime.now()
        wed = now - timedelta(days=(now.weekday() + 5) % 7)
        weds = []
        num_weeks = self.num_weeks
        while num_weeks > 0:
            weds.append(wed.strftime('%Y/%Y_%m_%d'))
            wed -= timedelta(days=7)
            num_weeks -= 1
        return weds

    def get_report_urls(self):
        urls = []
        for report_day in self.get_report_days():
            urls.append(BASE_URL % report_day)
        return urls

    def next_day_url(self, url):
        m = re.search(r'\d{4}_\d{2}_\d{2}', url)
        if m:
            day = datetime.strptime(m.group(0), '%Y_%m_%d')
            next_day = (day + timedelta(days=1)).strftime('%Y_%m_%d')
            return re.sub(r'\d{4}_\d{2}_\d{2}', next_day, url)
        else:
            return url

    def get_inventory(self, url):
        res = requests.get(url)
        if 'File Not Found' in res.content:
            res = requests.get(self.next_day_url(url))
        csvfile = StringIO.StringIO(res.content)
        reader = csv.reader(csvfile)
        try:
            for row in reader:
                if row[0] == 'Commercial (Excluding SPR)':
                    return row[3]
        except Exception as e:
            print 'Caught exception in get_inventory: %s' % e
        return None

    def get_inventories(self):
        if self.inventories:
            return self.inventories
        for url in self.get_report_urls():
            sys.stdout.write('. ')
            sys.stdout.flush()
            self.inventories.append(self.get_inventory(url))
        print '\n'
        return self.inventories

    def to_csv(self):
        report_days = self.get_report_days()
        inventories = self.get_inventories()
        return '\n'.join(['%s    %s' % (day.split('/')[1], inventory) for day, inventory in zip(report_days, inventories)])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Print out the crude oil inventory change over specified number of weeks.')
    parser.add_argument('num_weeks', metavar='N', type=int, help='Number of weeks in the past to get inventory')
    args = parser.parse_args()
    obj = OilInventory(args.num_weeks)
    print obj.to_csv()
