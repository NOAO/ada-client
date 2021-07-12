# Unit tests for the NOIRLab Astro Data Archive API Client
# EXAMPLES:
#   python -m unittest tests.tests_api.ApiTest
#   python -m unittest tests.tests_api.ApiTest.test_find_3

# EXAMPLES:
#  python -m unittest tests.tests_api

# Python library
import unittest
from unittest import skip,mock,skipIf,skipUnless
import warnings
from pprint import pformat,pprint
from urllib.parse import urlparse
# Local Packages
from client.api import AdaClient
from tests.utils import tic,toc
# External Packages
# <none>

### vosia

#rooturl = 'https://astroarchive.noao.edu/' #@@@
#rooturl = 'https://marsnat1.pat.dm.noao.edu/' #@@@
rooturl = 'http://localhost:8020/' #@@@


class ApiTest(unittest.TestCase):
    """Test access to each endpoint of the Server API"""

    @classmethod
    def setUpClass(cls):
        # AdaApi object creation compares the version from the Server
        # against the one expected by the Client. Throws error if
        # the Client is a major version behind.
        cls.client = AdaClient(rooturl, verbose=False, limit=5)
        cls.timing = dict()
        cls.doc = dict()
        cls.count = dict()
        print(f'Running Client tests against Server: '
              f'{urlparse(rooturl).netloc.split(".")[0]}')

    @classmethod
    def tearDownClass(cls):
        print(f'\n## Times on: {urlparse(rooturl).netloc.split(".")[0]}')
        for k,v in cls.timing.items():
            print(f'##   {k}: elapsed={v:.1f} secs;'
                  f'\t{cls.count.get(k)}'
                  f'\t{cls.doc.get(k)}')

    def test_server(self):
        """Make sure we are using PROD server"""
        assert rooturl == 'https://astroarchive.noao.edu/'

    def test_version(self):
        """Get version of the NOIRLab Astro Data Archive server API"""
        version = self.client.version
        assert 6.0 <= version < 7.0


    ########################################
    ### find
    ###
    ## For tests run <2021-03-10 Wed>
    ## Times on: marsnat1
    ##   find_0: elapsed=2.8 secs;	709968	Count files
    ##   find_2: elapsed=0.3 secs;	None	Find files
    ##   find_3: elapsed=41.5 secs;	26200848	Count HDUs
    ##   find_4: elapsed=22.4 secs;	None	Find HDUs
    ## astroarchive:
    ## Times on: astroarchive
    ##   find_0: elapsed=55.3 secs;	None	Count files
    ##   find_2: elapsed=22.0 secs;	None	Find files

    def test_find_0(self):
        """Count files"""
        name = 'find_0'
        this = self.test_find_0
        jdata = {"outfields": ["md5sum"], "search":[]}
        tic()
        info, rows = self.client.find(jdata, rectype='file', count=True)
        self.timing['find_0'] = toc()
        #self.doc[name] = self.test_find_0.__doc__
        self.doc[name] = this.__doc__
        self.count[name] = rows[0].get('count')
        assert len(rows) == 1

#!    def test_find_1(self):
#!        """Generalized file/hdu search"""
#!        name = 'find_1'
#!        this = self.test_find_1
#!        jdata = {"outfields": ["md5sum"], "search":[]}
#!        tic()
#!        info, rows = self.client.find(jdata, rectype='file')
#!        self.timing[name] = toc()
#!        self.doc[name] = this.__doc__
#!        assert len(rows) == 5

    def test_find_2(self):
        """Find files"""
        name = 'find_2'
        this = self.test_find_2
        spec2 = {
            "outfields": ["md5sum", "archive_filename"],
            "search": [["instrument", "decam"]]}
        tic()
        info, rows = self.client.find(spec2, rectype='file')
        self.timing[name] = toc()
        self.doc[name] = this.__doc__
        assert len(rows) == 5

    def test_find_3(self):
        """Count HDUs"""
        name = 'find_3'
        this = self.test_find_3
        jdata = {"outfields": ["hdu:hdu_idx"], "search":[]}
        tic()
        info, rows = self.client.find(jdata, rectype='hdu',
                                  count=True, verbose=True)
        self.timing[name] = toc()
        self.doc[name] = this.__doc__
        self.count[name] = rows[0].get('count')
        assert len(rows) == 1

    @skipIf(rooturl == 'https://astroarchive.noao.edu/',
            "Something wrong on PROD, this takes too long")
    def test_find_4(self):
        """Find HDUs"""
        name = "find_4"
        this = self.test_find_4
        # Only works with rectype='hdu'
        spec3 = {
            "outfields": ["exposure", "ifilter",
                          "hdu:ra_min", "hdu:ra_max",
                          "hdu:dec_min", "hdu:dec_max"],
            "search": [["instrument", "decam"],
                       ["proc_type", "instcal"]]}
        tic()
        info, rows = self.client.find(spec3, rectype='hdu', count=False)
        #print(f'find_4 info={pformat(info)} rows={pformat(rows)}')
        self.timing[name] = toc()
        self.doc[name] = this.__doc__
        assert len(rows) == 5
        #assert 'count' in rows[0]

    def test_find_5(self):
        """Invalid search spec. Say what is wrong with spec."""
        try:
            bad_spec = {'foobar': 99}
            info, rows = self.client.find(bad_spec, rectype='file')
        except Exception as err:
            #!print(f'Exception using find: {bad_spec}):{err}')
            expected = ('400 Client Error: Bad Request for url: '
                        'https://astroarchive.noao.edu/api/adv_search/'
                        'find/?rectype=file&limit=5&format=json')
            assert expected, err
        else:
            assert False, "Did not get expected exception"

#!    # @tag('ads','find')
#!    def test_find_d0(self):
#!        """Find using default search spec."""
#!        url = f'{adsurl}/find/?rectype=file&limit=0&offset=0'
#!        jdata = default_jdata
#!        #self.json_expected(url, 'expads.find_0', jdata=jdata, show=showads)
#!        info, *rows = self.json_response(url, jdata=jdata,
#!                                         exp='expads.find_0', show=showads)
#!        self.assertJSONEqual(json.dumps(info), json.dumps(expads.find_0_info))
#!        self.assertJSONEqual(json.dumps(rows), json.dumps(expads.find_0_rows))
#!
#!    # @tag('ads','find')
#!    def test_find_d1(self):
#!        """Find files owned by given user"""
#!        url = f'{adsurl}/find/?rectype=file&format=json&limit=None'
#!        jdata = {"outfields": ["proposal", "archive_filename"],
#!                 "search": [["user", "resta"]]}
#!        info, *rows = self.json_response(url, jdata=jdata,
#!                                         exp='expads.find_1', show=showads)
#!        self.assertJSONEqual(json.dumps(info), json.dumps(expads.find_1_info))
#!
#!    # @tag('ads','find')
#!    def test_find_d2(self):
#!        '''Render results as CSV'''
#!        url = f'{adsurl}/find/?rectype=file&format=csv&limit=2&sort=md5sum'
#!        jdata = default_jdata
#!        response = self.client.post(url, jdata,
#!                                    content_type='application/json')
#!        #showads = True
#!        if showads:
#!            print(f'DBG find_2: response={response.content}')
#!        self.assertEqual(response.content.decode("utf-8"),
#!                         expads.find_2,
#!                         'Actual to Expected')
#!
#!    # @tag('ads','find')
#!    def test_find_d3(self):
#!        '''Render results as XML'''
#!        url = f'{adsurl}/find/?rectype=file&format=xml&limit=2&sort=md5sum'
#!        jdata = {"outfields": ["md5sum"],"search": []}
#!        response = self.client.post(url, jdata,
#!                                    content_type='application/json')
#!        #showads = True
#!        if showads:
#!            print(f'DBG find_3: response={response.content}')
#!        self.assertEqual(response.content.decode("utf-8"),
#!                         expads.find_3,
#!                         'Actual to Expected')
#!    # @tag('ads','find')
#!    def test_find_d4(self):
#!        '''Invalid search spec. Missing section.'''
#!        url = f'{adsurl}/find/?rectype=file&format=xml&limit=2'
#!        jdata = {}
#!        self.error_expected(url, 'expads.find_4', jdata, show=showads)
#!
#!    # @tag('ads','find')
#!    def test_find_d5(self):
#!        '''Invalid search spec. Extra section.'''
#!        url = f'{adsurl}/find/?rectype=file&format=xml&limit=2'
#!        jdata = {"outfields": ["md5sum"],  "search": [], "nogood": []}
#!        self.error_expected(url, 'expads.find_5', jdata, show=showads)
#!
#!    # @tag('ads','find')
#!    def test_find_d6(self):
#!        """Get count of matches only. Use default search spec."""
#!        url = f'{adsurl}/find/?rectype=file&format=json&limit=2&count=Y'
#!        jdata = default_jdata
#!        self.json_expected(url, 'expads.find_6', jdata=jdata, show=showads)
#!
#!    # @tag('ads','find')
#!    def test_find_d7(self):
#!        """Invalid: HDU records with AUX output but no search constraint."""
#!        url = f'{adsurl}/find/?rectype=hdu&format=json&limit=2&count=Y'
#!        jdata = {"outfields": ["exposure", "ifilter", "AIRMASS",
#!                               "hdu:ra_min", "hdu:ra_max",
#!                               "hdu:dec_min", "hdu:dec_max",
#!                               "hdu:FWHM", "hdu:AVSKY"],
#!                 "search":[]}
#!        self.error_expected(url, 'expads.find_7', jdata, show=showads)
#!
#!    # @tag('ads','find')
#!    def test_find_d8(self):
#!        """Sort results per user keys. Duplicates of file so use 2 keys."""
#!        url = f'{adsurl}/find/?rectype=hdu&format=json&limit=10&sort=archive_filename,hdu_idx'
#!        jdata = {"outfields":
#!                 ["md5sum", "archive_filename", "original_filename"],
#!                 "search":[]}
#!        self.json_expected(url, 'expads.find_8', jdata=jdata, show=showads)
#!
#!    # @tag('ads','find')
#!    def test_find_d9(self):
#!        """Invalid key for sort results."""
#!        url = f'{adsurl}/find/?rectype=hdu&format=json&limit=10&sort=foo'
#!        jdata = {"outfields":
#!                 ["md5sum", "archive_filename", "original_filename"],
#!                 "search":[]}
#!        self.error_expected(url, 'expads.find_9', jdata, show=showads)
#!
#!    # @tag('ads','find')
#!    def test_find_d10(self):
#!        """Use offset (implied sort). Warning in results."""
#!        url = f'{adsurl}/find/?rectype=file&offset=2&limit=5'
#!        jdata = {"outfields": ["md5sum", "archive_filename"],
#!                 "search":[]}
#!        self.json_expected(url, 'expads.find_10', jdata=jdata, show=showads)
#!
#!    # @tag('ads','find')
#!    def test_find_d11(self):
#!        """Use offset, explicit same as implicit sort. """
#!        url = f'{adsurl}/find/?rectype=file&offset=2&limit=5&sort=md5sum'
#!        jdata = {"outfields": ["md5sum", "archive_filename"],
#!                 "search":[]}
#!        self.json_expected(url, 'expads.find_11', jdata=jdata, show=showads)
#!
#!    # @tag('ads','find')
#!    def test_find_d12(self):
#!        """Use offset, new explicit sort. No warning in results."""
#!        url = f'{adsurl}/find/?rectype=file&offset=2&limit=5&sort=archive_filename'
#!        jdata = {"outfields": ["md5sum", "archive_filename"],
#!                 "search":[]}
#!        self.json_expected(url, 'expads.find_12', jdata=jdata, show=showads)
#!
#!    # @tag('ads','find')
#!    def test_find_d13(self):
#!        """2 small pages same as one big one."""
#!        jdata = {"outfields": ["md5sum", "archive_filename"], "search":[]}
#!        furl = f'{adsurl}/find/?rectype=file'
#!        #!matches0 = self.json_response(furl, jdata=jdata)
#!        matches1a = self.json_response(furl+'&offset=0&limit=5', jdata=jdata)
#!        matches1b = self.json_response(furl+'&offset=5&limit=5', jdata=jdata)
#!        matches2 = self.json_response(furl+'&sort=md5sum&limit=10', jdata=jdata)
#!        #!print(f'matches0={pformat(matches0)}\n'
#!        #!      f'matches1a={pformat(matches1a)}\n'
#!        #!      f'matches1b={pformat(matches1b)}\n'
#!        #!      f'matches2={pformat(matches2)}\n')
#!        # only compare rows (exclude META)
#!        self.assertListEqual(matches1a[1:] + matches1b[1:], matches2[1:])
#!
#!    # @@@ offset=0 vs sort=md5sum (assert same records, diff meta)
#!    # @@@ A(offset=0,lim10), B(offset=5,lim5); assert(A[5:] == B)
#!
#!    # @tag('ads','find')
#!    def test_find_d14(self):
#!        """Do not return PROD url on DEV or PAT. NAT-568"""
#!        url = f'{adsurl}/find/?rectype=file&limit=2'
#!        jdata = {"outfields": ["md5sum", "url"],
#!                 "search":[]}
#!        naturi = self.factory.get(url).build_absolute_uri('/api/')
#!        ahost = urllib.parse.urlparse(naturi).netloc.split('.')[0]
#!        matches = self.json_response(url, jdata=jdata, show=showads)
#!        uhost = urllib.parse.urlparse(matches[1]['url']).netloc.split('.')[0]
#!        self.assertEqual(ahost, uhost)

    ########################################
    ### retrieve
    ###
    def test_retrieve_1(self):
        fid = '142584cb29e16fbc5c756024f1a79098'
        ok = self.client.retrieve(fid,'foo.fits')
        assert ok

    ########################################
    ### vosearch
    ###
    @skip('for now')
    def test_vosearch_1(self):
        """SIA search for files by ROI"""
        name = "vosearch_1"
        tic()
        votable = self.client.vosearch(ra=194.5, dec=-18.0, size=3.0,
                                   rectype='hdu')
        print(f'vosearch_1 actual={votable}')
        self.timing[name] = toc()
        assert len(votable) == 5, f'Got {len(votable)}'

##############################################################################

if __name__ == '__main__':
    unittest.main()
