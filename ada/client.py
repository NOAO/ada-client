# Python Standard Library
from urllib.parse import urlencode
from enum import Enum,auto
from pprint import pformat as pf
from pathlib import Path, PosixPath
from warnings import warn
import json
# Local Packages
#!import helpers.conf
# External Packages
import requests
from deprecated import deprecated

# Upload to PyPi (in venv):
#   bump version in ../setup.py
#   python3 -m build --wheel
#   twine upload dist/*

class _Rec(Enum):
    File = auto()
    Hdu = auto()


_PROD = 'https://astroarchive.noirlab.edu/'

class AdaClient():
    """Astro Data Archive Client.
    Instance creation compares the version from the Server
    against the one expected by the Client. Throws error if
    the Client is a major version or more behind.
    """
    KNOWN_GOOD_API_VERSION = 6.0  #@@@ Change this when Server version increments

    def __init__(self, url=_PROD,
                 verbose=False, limit=10, email=None,  password=None):
        self.rooturl=url.rstrip("/")
        self.apiurl = f'{self.rooturl}/api'
        self.adsurl = f'{self.rooturl}/api/adv_search'
        self.siaurl = f'{self.rooturl}/api/sia'
        self.categoricals = None
        self.token = None
        self.apiversion = None
        self.verbose = verbose
        self.limit = limit
        self.email = email
        if email is not None:
            res = requests.post(f'{self.apiurl}/get_token/',
                                json=dict(email=email, password=password))
            res.raise_for_status()
            if res.status_code == 200:
                self.token = res.json()
            else:
                self.token = None
                msg = (f'Credentials given '
                       f'(email="{email}", password={password}) '
                       f'could not be authenticated. Therefore, you will '
                       f'only be allowed to retrieve PUBLIC files. '
                       f'You can still get any metadata.' )
                raise Exception(msg)
        # Get API Version
        self.apiversion = float(requests.get(f'{self.apiurl}/version/').content)

        if (int(self.apiversion) - int(AdaClient.KNOWN_GOOD_API_VERSION)) >= 1:
            msg = (f'The helpers.api module is expecting an older '
                   f'version of the {self.rooturl} API services. '
                   f'Please upgrade to latest "aa_wrap".  '
                   f'This Client expected version '
                   f'{AdaClient.KNOWN_GOOD_API_VERSION} but got '
                   f'{self.apiversion} from the API.')
            raise Exception(msg)


    def retrieve(self, fileid, outfile, hdu=None):
        """Download a FITS file.

        :param fileid: File ID of FITS file in the Archive.
        :param outfile: Local full path that will be overwritten with FITS file.
        :param hdu: Indices of HDUs to include in file (default: include all)
        :returns: True on success
        :rtype: boolean

        """
        # VALIDATE params @@@

        ## 401 Unauthorized: File is proprietary and logged in user is
        ##     not authorized.
        ## 403 Forbidden: File is proprietary and user is not logged in.
        ## 404 Not Found: File-ID does not exist in Archive.
        qparams = '' if hdu is None else f'/?hdu={hdu}'
        url = f'{self.apiurl}/retrieve/{fileid}/{qparams}'
        if self.token is None:
            res = requests.get(url)
        else:
            res = requests.get(url, headers=dict(Authorization=self.token))
        try:
            res.raise_for_status()
        except Exception as err:
            print(f"Could not get token: {res}")
            # Get propid so to help figure out why request failed
            info,rows = self.find({"outfields": ["proposal"],
                                     "search":[["md5sum",fileid]]})
            raise Exception(f"{str(err)}"
                            f"; Email={self.email} must be authorized for"
                            f" Proposal={rows[0]['proposal']}")

        with open(outfile,'wb') as fits:
            fits.write(res.content)
        return True

    @property
    def file_count(self):
        res = self.find({"outfields": ["md5sum"], "search":[]},count=True)
        return(res[1][0]["count"])

    def find(self,
             jspec={"outfields":["md5sum"],"search":[]},
             count=False, format='json', limit=False, offset=None,
             rectype='file', sort=None,
             verbose=False):
        """Get metadata records that match a search specification.

        :param jspec: The search specification (@@@ more info)
        :param rectype: Type of rows/records to return ('file' or 'hdu')
        :param limit: The maximum number of rows to return
        :param format: The format of the result ('csv', 'xml', default='json')
        :returns: Header info and Rows
        :rtype: tuple (info,rows)

        """
        # VALIDATE params @@@
        maxhdu = 1000000
        verbose = verbose or self.verbose
        lim = None if limit is None else (limit or self.limit)
        if (lim is None) and (rectype == 'hdu'):
            warn(f'The api.find() function does not allow limit=None'
                 f' when rectype="hdu".  This is because the number of'
                 f' records that may be returned is on the order of'
                 f' half a billion.  A default limit={maxhdu} has been used.'
                 f' A future version will allow paging through results. ',
                 RuntimeWarning)
            lim = maxhdu

        uparams =dict(rectype=rectype,
                      limit=lim,
                      format=format)
        if count:
            uparams['count'] = 'Y'
        qstr = urlencode(uparams)

        url = f'{self.adsurl}/find/?{qstr}'
        if verbose:
            print(f'Search using "{url}" with: {json.dumps(jspec)}')
        res = requests.post(url, json=jspec) # @@@
        res.raise_for_status()

        if res.status_code != 200:
            raise Exception(res)

        if format == 'csv':
            return(res.content)
        elif format == 'xml':
            return(res.content)
        else: #'json'
            result = res.json()
            info = result.pop(0)
            rows = result
            if verbose:
                print(f'info={pf(info)}')
                #print(f'rows={pf(rows)}')
            return(info, rows)

#!    @deprecated(reason='Use "find" instead.')
#!    def search(self, jspec, limit=False, format='json'):
#!        """Search metadata according to jspec'
#!
#!        :param jspec: The search specification (@@@ more info)
#!        :param limit: The maximum number of rows to return
#!        :param format: The format of the result ('csv', 'xml', default='json')
#!        :returns: Header info and Rows
#!        :rtype: tuple (info,rows)
#!
#!        """
#!
#!        # VALIDATE params @@@
#!        qstr = urlencode(dict(limit=None if limit is None else (limit or self.limit),
#!                              format=format))
#!        t = 'h' if self.type == _Rec.Hdu else 'f'
#!        url = f'{self.adsurl}/{t}asearch/?{qstr}'
#!        if self.verbose:
#!            print(f'Search invoking "{url}" with: {jspec}')
#!        res = requests.post(url, json=jspec)
#!        res.raise_for_status()
#!        if self.verbose:
#!            print(f'Search status={res.status_code} res={res.content}')
#!
#!        if res.status_code != 200:
#!            raise Exception(res)
#!
#!        if format == 'csv':
#!            return(dict(format=format), res.content)
#!        elif format == 'xml':
#!            return(dict(format=format), res.content)
#!        else: #'json'
#!            result = res.json()
#!            info = result.pop(0)
#!            rows = result
#!            if self.verbose:
#!                print(f'info={pf(info)} rows={pf(rows)}')
#!            return(info, rows)

    def vosearch(self, ra, dec, size,
                 rectype='file', format='votable', limit=None):
        """SIA search by region of interest given by RA, DEC, and size.

        :param ra: right-ascension of the field center,
                   in decimal degrees using the ICRS coordinate system.
        :param dec: declination of the field center,
                    in decimal degrees using the ICRS coordinate system.
        :param size: The coordinate angular size of the region given
                     in decimal degrees. SINGLE VALUE for now. Example: '0.3'
        :param limit: The maximum number of rows to return
        :param format: The format of the result ('csv', 'xml', default='json')
        :returns: Header info and Rows
        :rtype: tuple (info,rows)

        """
        voep = 'vohdu' if rectype=='hdu' else 'voimg' # VO EndPoint
        qstr = urlencode(
            dict(POS=f'{ra},{dec}',
                 SIZE=size,
                 limit=None if limit is None else (limit or self.limit),
                 format=format))
        url = f'{self.siaurl}/{voep}?{qstr}'
        if self.verbose:
            print(f'Search invoking "{url}" with: ra={ra}, dec={dec}, '
                  f'size={size}')
        res = requests.get(url)
        res.raise_for_status()
        if self.verbose:
            print(f'Search status={res.status_code} res={res.content}')

        if res.status_code != 200:
            raise Exception(f'status={res.status_code} content={res.content}')

        if format == 'json':
            result = res.json()
            info = result.pop(0)
            rows = result
            return(info, rows)
        else:
            return(res.content)


    def check_version(self):
        """Insure this library in consistent with the API version.

        :returns: True if consistent, otherwise raise exception
        :rtype: boolean

        """
        res = requests.get(f"{self.apiurl}​/version​/")
        res.raise_for_status()
        return(True)

    def _get_categoricals(self):
        if self.categoricals is None:
            url = f'{self.adsurl}/cat_lists/'
            res = requests.get(url)
            res.raise_for_status()
            self.categoricals = res.json()  # dict(catname) = [val1, val2, ...]
        return(self.categoricals)

    def _get_aux_fields(self, instrument, proctype):
        # @@@ VALIDATE instrument, proctype, type
        t = 'hdu' if self.type == _Rec.Hdu else 'file'
        url = f'{self.adsurl}/aux_{t}_fields/{instrument}/{proctype}/'
        res = requests.get(url)
        res.raise_for_status()
        print(f"url={url}; res={res}; content={res.content}")
        return(res.json())

    def _get_core_fields(self):
        t = 'hdu' if self.type == _Rec.Hdu else 'file'
        # @@@ VALIDATE instrument, proctype, type
        res = requests.get(f'{self.adsurl}/core_{t}_fields/')
        res.raise_for_status()
        return(res.json())

    @property
    def version(self):
        """Return version of Rest API used by this module.

        If the Rest API changes such that the Major version increases,
        a new version of this module will likely need to be used.

        :returns: API version
        :rtype: float

        """
        if self.apiversion is None:
            response = self.requests.get(f'{self.apiurl}/version',
                                         timeout=self.TIMEOUT,
                                         cache=True)
            self.apiversion = float(response.content)
        return self.apiversion




# REMOVED in favor of "find" which allows mix of File and HDU in search spec
#!class FitsFile(AdaApi):
#!    """Object for getting FitsFile metadata and pixels.
#!
#!    This is faster than HduFile since it searches about 40x fewer records.
#!    """
#!
#!    def __init__(self,
#!                 url=_PROD,
#!                 verbose=False,
#!                 limit=10,
#!                 email=None,  password=None):
#!        """Create object for accessing FitsFile metadata and pixels.
#!
#!        :param url: Archive server to use.
#!        :param limit: Maxumim number of File records to return.
#!        :param verbose: Enable verbose output iff True.
#!        :param email: PI email. Only needed for download of proprietary files.
#!        :param password: PI password.
#!                         Only needed for download of proprietary files.
#!        """
#!
#!        super().__init__(url=url.rstrip("/"), verbose=verbose,
#!                         email=email, password=password)
#!        self.type = _Rec.File
#!        self.limit = limit
#!
#!    def retrieve(self, fileid, outfile, hdu=None):
#!        """Download a FITS file.
#!
#!        :param fileid: File ID of FITS file in the Archive.
#!        :param outfile: Local full path that will be overwritten with FITS file.
#!        :param hdu: Indices of HDUs to include in file (default: include all)
#!        :returns: True on success
#!        :rtype: boolean
#!
#!        """
#!        # VALIDATE params @@@
#!
#!        ## 401 Unauthorized: File is proprietary and logged in user is not authorized.
#!        ## 403 Forbidden: File is proprietary and user is not logged in.
#!        ## 404 Not Found: File-ID does not exist in Archive.
#!        qparams = '' if hdu is None else f'/?hdu={hdu}'
#!        url = f'{self.apiurl}/retrieve/{fileid}/{qparams}'
#!        if self.token is None:
#!            res = requests.get(url)
#!        else:
#!            res = requests.get(url, headers=dict(Authorization=self.token))
#!        try:
#!            res.raise_for_status()
#!        except Exception as err:
#!            print(f"Could not get token: {res}")
#!            # Get propid so to help figure out why request failed
#!            info,rows = self.search({"outfields": ["proposal"],
#!                                     "search":[["md5sum",fileid]]})
#!            raise Exception(f"{str(err)}"
#!                            f"; Email={self.email} must be authorized for"
#!                            f" Proposal={rows[0]['proposal']}")
#!
#!        #!fullpath = PosixPath(local_file_path).expanduser()
#!        #!with open(fullpath,'wb') as fits:
#!        #!    fits.write(res.content)
#!        #outfile.write(res.content)
#!        with open(outfile,'wb') as fits:
#!            fits.write(res.content)
#!        return True
#!
# REMOVED in favor of "find" which allows mix of File and HDU in search spec
#!class FitsHdu(AdaApi):
#!    """Object for getting FitsHdu metadata and pixels.
#!
#!    This is slower than FitsFile since it searches about 40x more records.
#!    """
#!
#!    def __init__(self,
#!                 url=_PROD,
#!                 limit=20,
#!                 verbose=False,
#!                 email=None,  password=None):
#!        """Create object for accessing FitsHdu metadata and pixels.
#!
#!        :param url: Archive server to use.
#!        :param limit: Maxumim number of HDU records to return.
#!        :param verbose: Enable verbose output iff True.
#!        :param email: PI email. Only needed for download of proprietary files.
#!        :param password: PI password.
#!                         Only needed for download of proprietary files.
#!
#!        """
#!        super().__init__(url=url.rstrip('/'), verbose=verbose,
#!                         email=email, password=password)
#!        self.type = _Rec.Hdu
#!        self.limit = limit

##############################################################################
