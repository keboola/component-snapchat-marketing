import dateparser
import datetime
import json
import logging
import pytz
import sys
from keboola.component import UserException
from keboola.component.base import ComponentBase, sync_action
from keboola.component.sync_actions import ValidationResult, MessageType
from snapchat.client import SnapchatClient
from snapchat.result import SnapchatWriter, SnapchatStatisticsWriter


KEY_DOWNLOAD_OBJECTS = 'statisticsObjects'
KEY_DATES_ATTR = 'dateSettings'
KEY_ATTRIBUTION_ATTR = 'attributionSettings'
KEY_QUERY = 'query'

KEY_DATES_START = 'startDate'
KEY_DATES_END = 'endDate'

KEY_ATTRIBUTION_GRANULARITY = 'granularity'
KEY_ATTRIBUTION_SWIPE = 'windowSwipe'
KEY_ATTRIBUTION_VIEW = 'windowView'

MANDATORY_PARAMS = []

AUTH_APPKEY = 'appKey'
AUTH_APPSECRET = '#appSecret'
AUTH_APPDATA = '#data'
AUTH_APPDATA_REFRESHTOKEN = 'refresh_token'

SUPPORTED_OBJECTS = ['campaigns', 'adsquads', 'ads']
SUPPORTED_GRANULARITY = ['HOUR', 'DAY']
SUPPORTED_WINDOW_VIEW = ["1_HOUR", "3_HOUR", "6_HOUR", "1_DAY", "7_DAY", "28_DAY"]
SUPPORTED_WINDOW_SWIPE = ["1_DAY", "7_DAY", "28_DAY"]

DATE_CHUNK_FORMAT = '%Y-%m-%d'

class SnapchatComponent(ComponentBase):

    def __init__(self):
        ComponentBase.__init__(self, required_parameters=MANDATORY_PARAMS)
        self.parseAuthorization()
        self.client = SnapchatClient(self.varRefreshToken, self.varAppKey, self.varAppSecret)

        self.writerOrganizations = SnapchatWriter(self.data_path, 'organizations')
        self.writerAdaccounts = SnapchatWriter(self.data_path, 'adaccounts')
        self.writerCampaigns = SnapchatWriter(self.data_path, 'campaigns')
        self.writerAdsquads = SnapchatWriter(self.data_path, 'adsquads')
        self.writerCreatives = SnapchatWriter(self.data_path, 'creatives')
        self.writerAds = SnapchatWriter(self.data_path, 'ads')

        self.checkParameters()

        if self.paramObjects != []:
            self.writerStatistics = SnapchatStatisticsWriter(self.data_path, metricFields=self.paramQuery)

        self.paramDateChunks = self.split_dates_to_chunks(self.paramStartDate, self.paramEndDate,
                                                          28 if self.paramGranularity == 'DAY' else 6,
                                                          strformat=DATE_CHUNK_FORMAT)

        logging.debug(self.paramDateChunks)

    def checkParameters(self):

        _objects = self.cfg_params.get(KEY_DOWNLOAD_OBJECTS, [])
        logging.debug(_objects)
        _diff = set(_objects) - set(SUPPORTED_OBJECTS)

        if len(_diff) > 0:
            logging.error(f"Unsupported objects {_diff} in parameter \"downloadForObjects\".")
            sys.exit(1)

        else:
            self.paramObjects = _objects

        _dates = self.cfg_params.get(KEY_DATES_ATTR, {})
        _startDate = dateparser.parse(_dates.get(KEY_DATES_START, '30 days ago'))
        _endDate = dateparser.parse(_dates.get(KEY_DATES_END, 'yesterday'))

        if _startDate is None or _endDate is None:

            logging.error(' '.join(["Invalid start date or end date. Read the \"dateparser\"",
                                    "documentation for correct usage and formats. The documentations is",
                                    "available at: https://dateparser.readthedocs.io/en/latest/."]))
            sys.exit(1)

        else:

            self.paramStartDate = _startDate
            self.paramEndDate = _endDate

            logging.debug(f"start: {_startDate}, end: {_endDate}.")

        _query = self.cfg_params.get(KEY_QUERY, '')
        _queryClean = list(set([m.strip() for m in _query.replace('\n', ',').split(',') if m.strip() != '']))

        if _queryClean == []:
            self.paramQuery = ['impressions', 'spend']

        else:
            self.paramQuery = _queryClean

        logging.debug(f"Query: {self.paramQuery}.")

        _attribution = self.cfg_params.get(KEY_ATTRIBUTION_ATTR, {})
        _granularity = _attribution.get(KEY_ATTRIBUTION_GRANULARITY, 'DAY')

        if _granularity not in SUPPORTED_GRANULARITY:
            logging.error(f"Unsupported granularity setting {_granularity}.")
            sys.exit(1)

        else:
            self.paramGranularity = _granularity

        _swipe = _attribution.get(KEY_ATTRIBUTION_SWIPE, '28_DAY')

        if _swipe not in SUPPORTED_WINDOW_SWIPE:
            logging.error(f"Unsupported swipe window setting {_swipe}.")
            sys.exit(1)

        else:
            self.paramWindowSwipe = _swipe

        _view = _attribution.get(KEY_ATTRIBUTION_VIEW, '1_DAY')

        if _view not in SUPPORTED_WINDOW_VIEW:
            logging.error(f"Unsupported swipe window setting {_view}.")
            sys.exit(1)

        else:
            self.paramWindowView = _view

    def getAuthorization(self):

        try:
            return self.configuration.config_data["authorization"]["oauth_api"]["credentials"]

        except KeyError:
            logging.error("Authorization is missing.")
            sys.exit(1)

    def parseAuthorization(self):

        authDict = self.getAuthorization()

        try:
            self.varAppKey = authDict[AUTH_APPKEY]
            self.varAppSecret = authDict[AUTH_APPSECRET]
            self.varRefreshToken = json.loads(authDict[AUTH_APPDATA])[AUTH_APPDATA_REFRESHTOKEN]

        except KeyError as e:
            logging.error("Key %s missing in authorization." % e)
            sys.exit(1)

    def normalizeTime(self, timezone):

        tz = pytz.timezone(timezone)
        chunks = []

        for chunk in self.paramDateChunks:

            _start = tz.localize(datetime.datetime.strptime(chunk['start_date'],
                                                            DATE_CHUNK_FORMAT)).replace(hour=0).isoformat()
            _end = tz.localize(datetime.datetime.strptime(chunk['end_date'],
                                                          DATE_CHUNK_FORMAT)).replace(hour=0).isoformat()

            chunks += [{'start_date': _start, 'end_date': _end}]

        return chunks

    def getAndWriteOrganizations(self):

        allOrgs = self.client.getOrganizations()
        self.writerOrganizations.writerow(allOrgs)
        self.varOrganizations = [org['id'] for org in allOrgs]

    def getAndWriteAdAccounts(self):

        allAdAccs = []

        for orgId in self.varOrganizations:
            allAdAccs += self.client.getAdAccounts(orgId)

        self.writerAdaccounts.writerow(allAdAccs)
        self.varAdAccs = {acc['id']: {"timezone": acc['timezone']} for acc in allAdAccs}

    def getAndWriteCampaigns(self, adAccountId):

        allCampaigns = self.client.getCampaignsForAdAccount(adAccountId)
        self.writerCampaigns.writerow(allCampaigns)

        if 'campaigns' in self.paramObjects:
            return [(c['id'], 'campaigns') for c in allCampaigns]

        else:
            return []

    def getAndWriteAdSquads(self, adAccountId):

        allAdSquads = self.client.getAdSquadsForAdAccount(adAccountId)
        self.writerAdsquads.writerow(allAdSquads)

        if 'adsquads' in self.paramObjects:
            return [(a['id'], 'adsquads') for a in allAdSquads]

        else:
            return []

    def getAndWriteCreatives(self, adAccountId):

        allCreatives = self.client.getCreativesForAdAccount(adAccountId)
        self.writerCreatives.writerow(allCreatives)

    def getAndWriteAds(self, adAccountId):

        allAds = self.client.getAdsForAdAccount(adAccountId)
        self.writerAds.writerow(allAds)

        if 'ads' in self.paramObjects:
            return [(a['id'], 'ads') for a in allAds]

        else:
            return []

    def run(self):

        self.getAndWriteOrganizations()
        logging.info("Organizations obtained.")

        self.getAndWriteAdAccounts()
        logging.info("Ad accounts obtained.")

        for adAccId, adAccIdSet in self.varAdAccs.items():

            logging.info(f"Starting download for ad account {adAccId}.")

            allStatObjects = []
            dates = self.normalizeTime(adAccIdSet['timezone'])

            logging.debug(dates)

            allStatObjects += self.getAndWriteCampaigns(adAccId)
            allStatObjects += self.getAndWriteAdSquads(adAccId)
            allStatObjects += self.getAndWriteAds(adAccId)
            self.getAndWriteCreatives(adAccId)

            for obj, end in allStatObjects:

                for dr in dates:

                    _measures = self.client.getStatistics(end, obj, ','.join(self.paramQuery), self.paramGranularity,
                                                          dr['start_date'], dr['end_date'], self.paramWindowSwipe,
                                                          self.paramWindowView)

                    self.writerStatistics.writerow(_measures)

            logging.info(f"Finished download for ad account {adAccId}.")

    @sync_action("list_organizations")
    def query_preview(self):

        formatted_output = self.client.getOrganizations()

        return ValidationResult(formatted_output, MessageType.SUCCESS)

"""
        Main entrypoint
"""
if __name__ == "__main__":
    try:
        comp = SnapchatComponent()
        # this triggers the run method by default and is controlled by the configuration.action parameter
        comp.execute_action()
    except UserException as exc:
        logging.exception(exc)
        exit(1)
    except Exception as exc:
        logging.exception(exc)
        exit(2)
