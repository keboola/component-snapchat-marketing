import logging
import os
import sys
import time
from kbc.client_base import HttpClientBase
from urllib.parse import urlparse, parse_qs


BASE_URL = 'https://adsapi.snapchat.com/v1/'
ACCESS_TOKEN_EXPIRATION = 1700
PAGINATION_LIMIT = 500


class SnapchatClient(HttpClientBase):

    def __init__(self, refreshToken, clientId, clientSecret):

        self.paramRefreshToken = refreshToken
        self.paramClientId = clientId
        self.paramClientSecret = clientSecret

        super().__init__(base_url=BASE_URL, status_forcelist=(429, 500, 502, 504))
        self.refreshAccessToken()

    def refreshAccessToken(self):

        urlRefresh = 'https://accounts.snapchat.com/login/oauth2/access_token'
        paramsRefresh = {
            'code': self.paramRefreshToken,
            'client_id': self.paramClientId,
            'client_secret': self.paramClientSecret,
            'grant_type': 'refresh_token'
        }

        reqRefresh = self.post_raw(urlRefresh, params=paramsRefresh)
        scRefresh, jsRefresh = reqRefresh.status_code, reqRefresh.json()

        if scRefresh == 200:

            self.varAccessToken = jsRefresh['access_token']
            logging.info("Access token refreshed.")

            self._auth_header = {'Authorization': f'Bearer {self.varAccessToken}'}
            self.varAccessTokenCreated = time.time()

        else:

            logging.info("Access token could not be refreshed. Received: %s - %s" % (scRefresh, jsRefresh))
            sys.exit(1)

    def _checkAndRefreshAccessToken(self):

        currentTime = time.time()
        timeDiff = int(currentTime - self.varAccessTokenCreated)

        if timeDiff >= ACCESS_TOKEN_EXPIRATION:
            self.refreshAccessToken()
        else:
            pass

    def getOrganizations(self):

        self._checkAndRefreshAccessToken()

        urlOrgs = os.path.join(self.base_url, 'me/organizations')

        reqOrgs = self.get_raw(urlOrgs)
        scOrgs, jsOrgs = reqOrgs.status_code, reqOrgs.json()

        if scOrgs == 200:

            logging.info("Organizations obtained successfully.")
            return [obj['organization'] for obj in jsOrgs['organizations']]

        else:

            logging.error("Could not obtain organizations. Received: %s - %s." % (scOrgs, jsOrgs))
            sys.exit(1)

    def _npGetAdAccounts(self, organizationId, cursor=None):

        self._checkAndRefreshAccessToken()

        urlAdAccs = os.path.join(self.base_url, f'organizations/{organizationId}/adaccounts')
        paramsAdAccs = {
            'limit': PAGINATION_LIMIT,
            'cursor': cursor
        }
        reqAdAccs = self.get_raw(urlAdAccs, params=paramsAdAccs)

        return reqAdAccs

    @staticmethod
    def _parseCursorParameter(urlToParse):

        if urlToParse is None:
            return None
        else:
            parsedUrl = urlparse(urlToParse)
            cursor = parse_qs(parsedUrl.query).get('cursor', [None])[0]
            return cursor

    def _npGetAdsForAdAccount(self, adAccountId, cursor=None):

        self._checkAndRefreshAccessToken()

        urlAds = os.path.join(self.base_url, f'adaccounts/{adAccountId}/ads')
        paramsAds = {
            'limit': PAGINATION_LIMIT,
            'cursor': cursor
        }
        reqAds = self.get_raw(urlAds, params=paramsAds)

        return reqAds

    def _npGetCampaignsForAdAccount(self, adAccountId, cursor=None):

        self._checkAndRefreshAccessToken()

        urlCampaigns = os.path.join(self.base_url, f'adaccounts/{adAccountId}/campaigns')
        paramsCampaigns = {
            'limit': PAGINATION_LIMIT,
            'cursor': cursor
        }

        reqCampaigns = self.get_raw(urlCampaigns, params=paramsCampaigns)

        return reqCampaigns

    def _npGetAdSquadsForAdAccount(self, adAccountId, cursor=None):

        self._checkAndRefreshAccessToken()

        urlAdSquads = os.path.join(self.base_url, f'adaccounts/{adAccountId}/adsquads')
        paramsAdSquads = {
            'limit': PAGINATION_LIMIT,
            'cursor': cursor
        }

        reqAdSquads = self.get_raw(urlAdSquads, params=paramsAdSquads)

        return reqAdSquads

    def _npGetCreativesForAdAccount(self, adAccountId, cursor=None):

        self._checkAndRefreshAccessToken()

        urlCreatives = os.path.join(self.base_url, f'adaccounts/{adAccountId}/creatives')
        paramsCreatives = {
            'limit': PAGINATION_LIMIT,
            'cursor': cursor
        }

        reqCreatives = self.get_raw(urlCreatives, params=paramsCreatives)

        return reqCreatives

    def _getPaginatedRequest(self, evalExpression, mappingObj, returnKey):

        if 'cursor' not in mappingObj:
            mappingObj['cursor'] = None

        moreRecords = True
        results = []
        while moreRecords is True:

            reqPagination = eval(evalExpression, None, mappingObj)
            scPagination, jsPagination = reqPagination.status_code, reqPagination.json()

            if scPagination == 200:

                results += [obj[returnKey] for obj in jsPagination[returnKey + 's']]
                nextPageUrl = jsPagination.get('paging', {}).get('next_link', None)
                nextPageCursor = self._parseCursorParameter(nextPageUrl)

                if nextPageCursor is None:
                    moreRecords = False
                else:
                    mappingObj['cursor'] = nextPageCursor

            else:

                logging.error("Could not obtain %s. Request to %s failed." % (returnKey, reqPagination.url))
                logging.error("Received: %s - %s." % (scPagination, jsPagination))
                sys.exit(1)

        return results

    def getAdsForAdAccount(self, adAccountId):

        evalAds = 'func(adAccId, cursor)'
        mapAds = {
            'adAccId': adAccountId,
            'func': self._npGetAdsForAdAccount
        }
        keyAds = 'ad'

        return self._getPaginatedRequest(evalAds, mapAds, keyAds)

    def getAdAccounts(self, organizationId):

        evalAdAccs = 'func(orgId, cursor)'
        mapAdAccs = {
            'func': self._npGetAdAccounts,
            'orgId': organizationId
        }
        keyAdAccs = 'adaccount'

        return self._getPaginatedRequest(evalAdAccs, mapAdAccs, keyAdAccs)

    def getCampaignsForAdAccount(self, adAccountId):

        evalCampaigns = 'func(adAccId, cursor)'
        mapCampaigns = {
            'adAccId': adAccountId,
            'func': self._npGetCampaignsForAdAccount
        }
        keyCampaigns = 'campaign'

        return self._getPaginatedRequest(evalCampaigns, mapCampaigns, keyCampaigns)

    def getAdSquadsForAdAccount(self, adAccountId):

        evalAdSquads = 'func(adAccId, cursor)'
        mapAdSquads = {
            'adAccId': adAccountId,
            'func': self._npGetAdSquadsForAdAccount
        }
        keyAdSquads = 'adsquad'

        return self._getPaginatedRequest(evalAdSquads, mapAdSquads, keyAdSquads)

    def getCreativesForAdAccount(self, adAccountId):

        evalCreatives = 'func(adAccId, cursor)'
        mapCreatives = {
            'adAccId': adAccountId,
            'func': self._npGetCreativesForAdAccount
        }
        keyCreatives = 'creative'

        return self._getPaginatedRequest(evalCreatives, mapCreatives, keyCreatives)

    def getStatistics(self, endpoint, endpointId, fields, granularity, startTime, endTime, windowSwipe, windowView):

        self._checkAndRefreshAccessToken()

        urlStatistics = os.path.join(self.base_url, endpoint, endpointId, 'stats')
        paramsStatistics = {
            'fields': fields,
            'granularity': granularity,
            'start_time': startTime,
            'end_time': endTime,
            'swipe_up_attribution_window': windowSwipe,
            'view_attribution_window': windowView
        }

        reqStatistics = self.get_raw(urlStatistics, params=paramsStatistics)
        scStatistics, jsStatistics = reqStatistics.status_code, reqStatistics.json()

        if scStatistics == 200:

            return [x['timeseries_stat'] for x in jsStatistics['timeseries_stats']]

        else:

            logging.error(f"Could not obtain statistics for {endpoint}, id: {endpointId}.")
            logging.error(f"Received: {scStatistics} - {jsStatistics}.")
            sys.exit(1)
