# Snapchat Marketing Extractor

A Snapchat marketing extractor allows users to download data about marketing campaigns and statistics via Snapchat Marketing API. To successfully download data, following prerequisities are required to be met:

- Snapchat account (create one at https://ads.snapchat.com/)
- access to Snapchat Matketing API (apply at https://developers.snapchat.com/apply/)

The extractor allows to download statistics for campaigns, adsquads and ads with all supported metrics from Snapchat with either hourly or daily granularity.

## Configuration

The full configuration of the Snapchat extractor can be found in the [component's repository](https://bitbucket.org/kds_consulting_team/kds-team.ex-snapchat-marketing/src/master/component_config/sample-config/).

The component needs to be authorized with valid Snapchat Marketing account via OAuth. Configuration parameters will be discussed in upcoming sections.

### Objects to download (`statisticsObjects`)

An array of objects, for which the statistics should be downloaded. One or multiple objects can be specified.
Allowed values are:

- campaigns,
- adsquads,
- ads.

Based on amount of data available for each endpoint, it might take a while to download all of the data. It is therefore recommended to only download data in the lowest accuracy needed. If nothing's specified, no statistics are downloaded and only campaigns, ad squads and ads are returned - without statistics.

### Start date and end date (`dateSettings.startDate` and `dateSettings.endDate`)

A date range, which defines the upper and lower boundary of downloaded statistics. Any supported format by [`dateparser` library](https://pypi.org/project/dateparser/) can be used, but it's recommended to stick by `YYYY-MM-DD` or `YYYY-MM-DD HH:MI:SS` format; or in case of relative date specification, use one of the following options: `2 months ago`, `10 days ago`, `2 hours ago`, `today`, `in 3 days`.

### Granularity (`attributionSettings.granularity`)

Defines a granularity by which the data should be download. Either `HOUR` - hourly data, or `DAY` - daily data is supported. `HOUR` granularity supports much smaller date window and will therefore require more calls to retrieve the data, consequently taking longer time to finish.

### Swipe-up and View attribution windows (`attributionSettings.windowSwipe` and `attributionSettings.windowView`)

Attributes of Snapchat Marketing API which define which attribution window to use for metric values returned. Useful if [variants of metrics](https://developers.snapchat.com/api/docs/#attribution-windows) are to be used.

### Metrics (`query`)

A comma-separated or new-line separated list of metrics, which will be downloaded for each object. For full list of metrics and their variations, please visit [Snapchat documentation](https://developers.snapchat.com/api/docs/#core-metrics).
