import csv
import json
import os

FIELDS_ORGANIZATIONS = ['id', 'updated_at', 'created_at', 'name', 'country', 'postal_code', 'locality', 'contact_name',
                        'contact_email', 'tax_id', 'address_line_1', 'administrative_district_level_1',
                        'accepted_term_version', 'configuration_settings', 'type', 'state', 'roles', 'my_display_name',
                        'my_invited_email', 'my_member_id']
JSON_FIELDS_ORGANIZATIONS = ['configuration_settings', 'roles']
PK_ORGANIZATIONS = ['id']

FIELDS_ADACCOUNTS = ['id', 'updated_at', 'created_at', 'name', 'type', 'status', 'organization_id',
                     'funding_source_ids', 'currency', 'timezone', 'advertiser_organization_id', 'billing_center_id',
                     'billing_type', 'agency_representing_client', 'client_paying_invoices', 'regulations']
JSON_FIELDS_ADACCOUNTS = ['funding_source_ids', 'regulations']
PK_ADACCOUNTS = ['id']

FIELDS_CAMPAIGNS = ['id', 'name', 'ad_account_id', 'status', 'objective', 'updated_at', 'created_at',
                    'start_time', 'end_time', 'lifetime_spend_cap_micro', 'daily_budget_micro', 'buy_model',
                    'regulations', 'measurement_spec']
JSON_FIELDS_CAMPAIGNS = ['regulations', 'measurement_spec']
PK_CAMPAIGNS = ['id']

FIELDS_ADSQUADS = ['id', 'name', 'campaign_id', 'status', 'updated_at', 'created_at', 'type', 'targeting',
                   'targeting_reach_status', 'placement', 'billing_event', 'bid_micro', 'auto_bid', 'target_bid',
                   'lifetime_budget_micro', 'start_time', 'end_time', 'optimization_goal', 'delivery_constraint',
                   'pacing_type']
JSON_FIELDS_ADSQUADS = ['targeting']
PK_ADSQUADS = ['id']

FIELDS_CREATIVES = ['id', 'updated_at', 'created_at', 'name', 'ad_account_id', 'type', 'packaging_status',
                    'review_status', 'review_status_details', 'shareable', 'forced_view_eligibility', 'headline',
                    'brand_name', 'call_to_action', 'render_type', 'top_snap_media_id', 'top_snap_crop_position',
                    'ad_product', 'app_install_properties', 'longform_video_properties', 'web_view_properties']
JSON_FIELDS_CREATIVES = ['app_install_properties', 'longform_video_properties', 'web_view_properties']
PK_CREATIVES = ['id']

FIELDS_ADS = ['id', 'name', 'ad_squad_id', 'creative_id', 'status', 'type', 'render_type', 'updated_at',
              'created_at', 'review_status']
JSON_FIELDS_ADS = []
PK_ADS = ['id']

FIELDS_STATISTICS = ['id', 'type', 'granularity', 'swipe_up_attribution_window', 'view_attribution_window',
                     'start_time', 'end_time']
PK_STATISTICS = ['id', 'type', 'granularity', 'swipe_up_attribution_window', 'view_attribution_window',
                 'start_time', 'end_time']


class SnapchatStatisticsWriter:

    def __init__(self, dataPath, tableName='statistics', metricFields=[]):

        self.paramPath = dataPath
        self.paramTable = 'statistics.csv'
        self.paramTablePath = os.path.join(self.paramPath, 'out/tables', self.paramTable)
        self.paramFields = FIELDS_STATISTICS + metricFields
        self.paramPrimaryKey = PK_STATISTICS

        self.createManifest()
        self.createWriter()

    def createManifest(self):

        template = {
            'incremental': True,
            'primary_key': self.paramPrimaryKey
        }

        path = self.paramTablePath + '.manifest'

        with open(path, 'w') as manifest:

            json.dump(template, manifest)

    def createWriter(self):

        self.writer = csv.DictWriter(open(self.paramTablePath, 'w'), fieldnames=self.paramFields,
                                     restval='', extrasaction='ignore', quotechar='\"', quoting=csv.QUOTE_ALL)
        self.writer.writeheader()

    def writerow(self, listToWrite):

        for stat in listToWrite:

            headerDict = {
                'id': stat['id'],
                'type': stat['type'],
                'granularity': stat['granularity'],
                'swipe_up_attribution_window': stat['swipe_up_attribution_window'],
                'view_attribution_window': stat['view_attribution_window']
            }

            for timeseries in stat['timeseries']:

                metricDict = timeseries['stats']
                metricDict['start_time'] = timeseries['start_time']
                metricDict['end_time'] = timeseries['end_time']

                self.writer.writerow({**headerDict, **metricDict})


class SnapchatWriter:

    def __init__(self, dataPath, tableName):

        self.paramPath = dataPath
        self.paramTableName = tableName
        self.paramTable = tableName + '.csv'
        self.paramTablePath = os.path.join(self.paramPath, 'out/tables', self.paramTable)
        self.paramFields = eval(f'FIELDS_{tableName.upper()}')
        self.paramJsonFields = eval(f'JSON_FIELDS_{tableName.upper()}')
        self.paramPrimaryKey = eval(f'PK_{tableName.upper()}')

        self.createManifest()
        self.createWriter()

    def createManifest(self):

        template = {
            'incremental': True,
            'primary_key': self.paramPrimaryKey
        }

        path = self.paramTablePath + '.manifest'

        with open(path, 'w') as manifest:

            json.dump(template, manifest)

    def createWriter(self):

        self.writer = csv.DictWriter(open(self.paramTablePath, 'w'), fieldnames=self.paramFields,
                                     restval='', extrasaction='ignore', quotechar='\"', quoting=csv.QUOTE_ALL)
        self.writer.writeheader()

    def writerow(self, listToWrite):

        for row in listToWrite:

            _dictToWrite = {}

            for key, value in row.items():

                if key in self.paramJsonFields:
                    _dictToWrite[key] = json.dumps(value)

                else:
                    _dictToWrite[key] = value

            self.writer.writerow(_dictToWrite)
