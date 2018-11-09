''' Crawl the running Docker site and verify all links give a 200 OK '''

import unittest
import re
import requests

class BrokenLinkTest(unittest.TestCase):
    ''' Base class for testing links '''

    def setUp(self):
        ''' Define some unique data for validation '''
        self.acceptable_codes = [200]

    def tearDown(self):
        ''' Destroy unique data '''
        self.domain = None
        self.acceptable_codes = None

    def request_prediction(self, url=None, coins=None):
        results=[]
        for coin in coins:
            r = requests.get('{}?coin={}'.format(url, coin), allow_redirects=False, verify=False)
            results.append(r)
        return list(zip(coins, results))

class CrawlSite(BrokenLinkTest):
    ''' Verify no broken links are present within blog '''
    def runTest(self):
        ''' Execute recursive request '''
        results = self.request_prediction("http://127.0.0.1:5000/predict", ['BTC', 'ETH'])
        for r in results:
            status=r[1].status_code
            coin=r[0]
            self.assertTrue(
                status in self.acceptable_codes,
                "Found {0} in return codes for coin: {1}".format(status, coin)
            )
