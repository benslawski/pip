from threading import *
from time import *
from httplib import *


class RateLogger:

    def __init__(self, currencies, logpath='', runtime=86400, lograte=900):
        self.currencies = currencies
        self.rates = dict(map(lambda k: (k, []), self.currencies))
        self.logpath = logpath
        self.runtime = runtime
        self.lograte = lograte

        self.logRates()
        self.dumpLogs()


    def logRates(self):
        starttime = time()
        while time() - starttime < self.runtime:
            worker_threads = map(lambda k: APICallerThread(k, self.rates), self.currencies)
            map(lambda k: k.start(), worker_threads)
            map(lambda k: k.join(), worker_threads)
            sleep(self.lograte - ((time() - starttime) % self.lograte))


    def dumpLogs(self):
        for currency in self.currencies:
            f = open(self.logpath + currency + '_' +  str(self.runtime) + '.dat', 'w')
            for datapnt in self.rates[currency]:
                f.write(datapnt[0] + '\t' + datapnt[1] + '\n')
            f.close()


class APICallerThread(Thread):

    def __init__(self, currency, datastore):
        Thread.__init__(self)
        self.currency = currency
        self.datastore = datastore


    def run(self):
        api = 'www.google.com'
        lookup = '/finance?q=CURRENCY%3A' + self.currency

        lookupdata = None

        max_attempts = 20
        attempts = 0
        while attempts < max_attempts:
            try:
                conn = HTTPConnection(api)
                conn.request("GET", lookup)

                results = conn.getresponse()
                assert(results.status == 200)
                lookupdata = results.read()
                conn.close()

                break

            ## bad status on return
            except AssertionError:
                conn.close()

                ## thats not a real lookup
                if results.status == 404:
                    print lookup, 'not found!'
                    break
                ## server is down, give it a bit
                elif results.status == 503:
                    print 'server overload, pausing', lookup
                    sleep(10.*random())
                ## server is really down, not the time to pull data
                elif results.status == 500:
                    print 'server crash, exiting'
                    break
                ## wtf happened?  log it
                else:
                    print results.status, lookup
                    sleep(10. * random())
    
            except Exception as e:
                print type(e), e.message, api, lookup
    
            attempts += 1
    
        if lookupdata:
            try:
                datapnt = self.parsePage(lookupdata)
                print datapnt
                self.datastore[self.currency].append(datapnt)
            except Exception as e:
                print self.currency, type(e), e.message


    ## TODO regex find values

    def parsePage(self, content):
        dumpfile = open('pagedump.txt', 'w')
        dumpfile.write(content)
        dumpfile.close()

        timestamp = content.split('<div id="ref_14546367_ldt" class="time">')[1] \
                           .split('<div id="ref_14546367_ldt" class="time">')[0] \
                           .strip()
        print timestamp

        timestep = 'None'
        exchange = content.split('<div id="currency_value" class="sfe-section">')[1] \
                          .split('</span>')[0] \
                          .split('<span class="bld">')[1] \
                          .split(' USD')[0]
        print exchange

        return timestamp, exchange



if __name__ == "__main__":
    currencies = ["GBP"]
##    currencies = ["GBP", "JPY", "EUR", "NOK"]
    logpath = 'data/'

    RateLogger(currencies, logpath=logpath, runtime=300, lograte=60) 
