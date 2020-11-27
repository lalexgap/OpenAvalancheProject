# AUTOGENERATED! DO NOT EDIT! File to edit: DataPipelineNotebooks/3.PrepMLData.ipynb (unless otherwise specified).

__all__ = ['PrepML']

# Cell
import xarray as xr
import numpy as np
import pandas as pd
from joblib import Parallel, delayed
import time
from functools import partial

from datetime import datetime
import datetime
import os

import pickle

# Cell
class PrepML:


    def __init__(self, data_root, interpolate=1, date_start='2015-11-01', date_end='2020-04-30', date_train_test_cutoff='2019-11-01'):
        """
        Initialize the class

        Keyword Arguments
        data_root: the root path of the data folders which contains the 4.GFSFiltered1xInterpolationZarr
        interpolate: the amount of interpolation applied in in the previous ParseGFS notebook (used for finding the correct input/output paths)
        date_start: Earlist date to include in label set (default: '2015-11-01')
        date_end: Latest date to include in label set (default: '2020-04-30')
        date_train_test_cutoff: Date to use as a cutoff between the train and test labels (default: '2019-11-01')
        """
        self.data_root = data_root
        self.interpolation = interpolate
        self.date_start = date_start
        self.date_end = date_end
        self.date_train_test_cutoff = date_train_test_cutoff
        self.nc_path = data_root + '/3.GFSFiltered'+ str(self.interpolation) + 'xInterpolation/'
        self.processed_path = data_root + '/4.GFSFiltered'+ str(self.interpolation) + 'xInterpolationZarr/'
        self.path_to_labels = data_root + 'CleanedForecastsNWAC_CAIC_UAC.V1.2013-2020.csv'
        self.ml_path = data_root + '/5.MLData'
        self.date_col = 'Day1Date'
        self.region_col = 'UnifiedRegion'
        self.parsed_date_col = 'parsed_date'
        if not os.path.exists(self.ml_path):
            os.makedirs(self.ml_path)

        #map states to regions for purposes of data lookup
        self.regions = {
            'Utah': ['Abajos', 'Logan', 'Moab', 'Ogden', 'Provo',
            'Salt Lake', 'Skyline', 'Uintas'],
            'Colorado': ['Grand Mesa Zone', 'Sangre de Cristo Range', 'Steamboat Zone', 'Front Range Zone',
            'Vail Summit Zone', 'Sawatch Zone', 'Aspen Zone',
            'North San Juan Mountains', 'South San Juan Mountains', 'Gunnison Zone'],
            'Washington': ['Mt Hood', 'Olympics', 'Snoqualmie Pass', 'Stevens Pass',
            'WA Cascades East, Central', 'WA Cascades East, North', 'WA Cascades East, South',
            'WA Cascades West, Central', 'WA Cascades West, Mt Baker', 'WA Cascades West, South'
            ]
        }


    @staticmethod
    def lookup_forecast_region(label_region):
        """
        mapping between region names as the labels and the forecasts have slightly different standards
        TODO: could add a unified mapping upstream in parseGFS files or in the label generation

        Keyword Arguments:
        label_region: region as defined in the labels file

        returns the region as defined in the features
        """
        if label_region == 'Mt Hood':
            return 'Mt Hood'
        elif label_region == 'Olympics':
            return 'Olympics'
        elif label_region == 'Cascade Pass - Snoq. Pass':
            return 'Snoqualmie Pass'
        elif label_region == 'Cascade Pass - Stevens Pass':
            return 'Stevens Pass'
        elif label_region == 'Cascade East - Central':
            return 'WA Cascades East, Central'
        elif label_region == 'Cascade East - North':
            return 'WA Cascades East, North'
        elif label_region == 'Cascade East - South':
            return 'WA Cascades East, South'
        elif label_region == 'Cascade West - Central':
            return 'WA Cascades West, Central'
        elif label_region == 'Cascade West - North':
            return 'WA Cascades West, Mt Baker'
        elif label_region == 'Cascade West - South':
            return 'WA Cascades West, South'
        elif label_region == 'Abajo':
            return 'Abajos'
        elif label_region == 'Logan':
            return 'Logan'
        elif label_region == 'Moab':
            return 'Moab'
        elif label_region == 'Ogden':
            return 'Ogden'
        elif label_region == 'Provo':
            return 'Provo'
        elif label_region == 'Salt Lake':
            return 'Salt Lake'
        elif label_region == 'Skyline':
            return 'Skyline'
        elif label_region == 'Uintas':
            return 'Uintas'
        elif label_region == 'Grand Mesa':
            return 'Grand Mesa Zone'
        elif label_region == 'Sangre de Cristo':
            return 'Sangre de Cristo Range'
        elif label_region == 'Steamboat & Flat Tops':
            return 'Steamboat Zone'
        elif label_region == 'Front Range':
            return 'Front Range Zone'
        elif label_region == 'Vail & Summit County':
            return 'Vail Summit Zone'
        elif label_region == 'Sawatch Range':
            return 'Sawatch Zone'
        elif label_region == 'Aspen':
            return 'Aspen Zone'
        elif label_region == 'Northern San Juan':
            return 'North San Juan Mountains'
        elif label_region == 'Southern San Juan':
            return 'South San Juan Mountains'
        elif label_region == 'Gunnison':
            return 'Gunnison Zone'
        else:
            return 'Got region ' + label_region + ' but its an unknown region'

    @staticmethod
    def date_to_season(d):
        """
        mapping of date to season

        Keyword Arguments
        d: datetime64

        returns season indicator
        """
        if d >= np.datetime64('2014-11-01') and d <= np.datetime64('2015-04-30'):
            return (np.datetime64('2014-11-01'), '14-15')
        elif d >= np.datetime64('2015-11-01') and d <= np.datetime64('2016-04-30'):
            return (np.datetime64('2015-11-01'), '15-16')
        elif d >= np.datetime64('2016-11-01') and d <= np.datetime64('2017-04-30'):
            return (np.datetime64('2016-11-01'), '16-17')
        elif d >= np.datetime64('2017-11-01') and d <= np.datetime64('2018-04-30'):
            return (np.datetime64('2017-11-01'), '17-18')
        elif d >= np.datetime64('2018-11-01') and d <= np.datetime64('2019-04-30'):
            return (np.datetime64('2018-11-01'), '18-19')
        elif d >= np.datetime64('2019-11-01') and d <= np.datetime64('2020-04-30'):
            return (np.datetime64('2019-11-01'), '19-20')
        else:
            #print('Unknown season ' + str(d))
            return (-1,'Unknown')


    def get_state_for_region(self, region):
        """
        Returns the state for a given region

        Keywork Arguments
        region: region we want to lookup the state for
        """
        for k in self.regions.keys():
            if region in self.regions[k]:
                return k

        raise Exception('No region with name ' + region)

    def prep_labels(self, overwrite_cache=False):
        """
        Preps the data and lable sets in to two sets, train & test

        Keyword Arguments
        overwrite_cache: True indicates we want to recalculate the lat/lon combos, False indicates use the values if they exist in the cache file (otherwise calcualte and cache it)

        returns the train & test sets
        """


        #maintaining this as a dict since the arrays are ragged and its more efficient this way
        #storing one sample for each region to get the lat/lon layout
        region_zones = []
        region_data = {}
        for region in self.regions.keys():
            for r in self.regions[region]:
                region_zones.append(r)
                region_data[r] = xr.open_dataset(self.nc_path + '15-16/' + '/Region_' + r + '_20160101.nc')

        #Read in all the label data
        self.labels = pd.read_csv(self.path_to_labels, low_memory=False,
                dtype={'Day1Danger_OctagonAboveTreelineEast': 'object',
                       'Day1Danger_OctagonAboveTreelineNorth': 'object',
                       'Day1Danger_OctagonAboveTreelineNorthEast': 'object',
                       'Day1Danger_OctagonAboveTreelineNorthWest': 'object',
                       'Day1Danger_OctagonAboveTreelineSouth': 'object',
                       'Day1Danger_OctagonAboveTreelineSouthEast': 'object',
                       'Day1Danger_OctagonAboveTreelineSouthWest': 'object',
                       'Day1Danger_OctagonAboveTreelineWest': 'object',
                       'Day1Danger_OctagonBelowTreelineEast': 'object',
                       'Day1Danger_OctagonBelowTreelineNorth': 'object',
                       'Day1Danger_OctagonBelowTreelineNorthEast': 'object',
                       'Day1Danger_OctagonBelowTreelineNorthWest': 'object',
                       'Day1Danger_OctagonBelowTreelineSouth': 'object',
                       'Day1Danger_OctagonBelowTreelineSouthEast': 'object',
                       'Day1Danger_OctagonBelowTreelineSouthWest': 'object',
                       'Day1Danger_OctagonBelowTreelineWest': 'object',
                       'Day1Danger_OctagonNearTreelineEast': 'object',
                       'Day1Danger_OctagonNearTreelineNorth': 'object',
                       'Day1Danger_OctagonNearTreelineNorthEast': 'object',
                       'Day1Danger_OctagonNearTreelineNorthWest': 'object',
                       'Day1Danger_OctagonNearTreelineSouth': 'object',
                       'Day1Danger_OctagonNearTreelineSouthEast': 'object',
                       'Day1Danger_OctagonNearTreelineSouthWest': 'object',
                       'Day1Danger_OctagonNearTreelineWest': 'object',
                       'SpecialStatement': 'object',
                       'image_paths': 'object',
                       'image_types': 'object',
                       'image_urls': 'object'})

        self.labels['parsed_date'] = pd.to_datetime(self.labels[self.date_col], format='%Y%m%d')

        metadata_cols = [self.date_col, self.region_col]
        label_cols = ['Day1DangerBelowTreeline', 'Day1DangerNearTreeline', 'Day1DangerAboveTreeline']
        self.labels[self.region_col] = self.labels.apply(lambda x : PrepML.lookup_forecast_region(x[self.region_col]), axis=1)
        self.labels = self.labels[self.labels[self.region_col]!='Unknown region']

        #ensure we are only using label data for regions we are looking at
        self.labels = self.labels[self.labels[self.region_col].isin(region_zones)]

        #add a season column
        tmp = pd.DataFrame.from_records(self.labels[self.parsed_date_col].apply(PrepML.date_to_season))
        self.labels['season'] = tmp[1]
        self.labels.reset_index(drop=True, inplace=True)

        #some region/seasons have excessive errors in the data, remove those
        self.labels = self.labels[self.labels['season'].isin(['15-16', '16-17', '17-18', '18-19'])]
        self.labels = self.labels[~self.labels.index.isin(self.labels[(self.labels['season']=='15-16') & (self.labels[self.region_col]=='Steamboat Zone')].index)]
        self.labels = self.labels[~self.labels.index.isin(self.labels[(self.labels['season']=='16-17') & (self.labels[self.region_col]=='Front Range Zone')].index)]

        #add extra labels which also allow us to have labels which indicate the trend in the avy direction
        #the thought here is that predicting a rise or flat danger is usually easier than predicting when
        #to lower the danger so seperating these in to seperate clases
        #TODO: this should be dynamic based on label passed in, not hard coded to above treeline
        labels_trends = pd.DataFrame()
        for r in self.labels[self.region_col].unique():
            for s in self.labels['season'].unique():
                region_season_df = self.labels[self.labels['season']==s]
                region_season_df = region_season_df[region_season_df[self.region_col]==r]
                if(len(region_season_df) == 0):
                    continue
                region_season_df.sort_values(by='parsed_date', inplace=True)
                region_season_df.reset_index(inplace=True, drop=True)
                region_season_df['Day1DangerAboveTreelineValue'] = region_season_df['Day1DangerAboveTreeline'].map({'Low':0, 'Moderate':1, 'Considerable':2, 'High':3})
                region_season_df.loc[0,'Day1DangerAboveTreelineWithTrend'] = region_season_df.iloc[0]['Day1DangerAboveTreeline'] + '_Initial'

                for i in range(1,len(region_season_df)):
                    prev = region_season_df.iloc[i-1]['Day1DangerAboveTreelineValue']
                    cur = region_season_df.loc[i,'Day1DangerAboveTreelineValue']
                    trend = '_Unknown'
                    if prev == cur:
                        trend = '_Flat'
                    elif prev < cur:
                        trend = '_Rising'
                    elif prev >  cur:
                        trend = '_Falling'

                    region_season_df.loc[i,'Day1DangerAboveTreelineWithTrend'] = region_season_df.iloc[i]['Day1DangerAboveTreeline'] + trend
                labels_trends = pd.concat([labels_trends,region_season_df])
        assert(len(labels_trends)==len(self.labels))
        self.labels = labels_trends

        lat_lon_union = pd.DataFrame()
        lat_lon_path = self.processed_path + 'lat_lon_union.csv'
        if overwrite_cache or not os.path.exists(lat_lon_path):
            #find union of all lat/lon/region to just grids with values
            #the process to filter the lat/lon is expensive but we need to do it here (1-5 seconds per region)
            #as the helps the batch process select relevant data
            for r in region_data.keys():
                print(r)
                region_df = region_data[r].stack(lat_lon = ('latitude', 'longitude')).lat_lon.to_dataframe()
                tmp_df = pd.DataFrame.from_records(region_df['lat_lon'], columns=['latitude', 'longitude'])
                indexes_to_drop = []
                for index, row in tmp_df.iterrows():
                    #TODO: there might be a more efficient way than doing this one by one?
                    if 0 == np.count_nonzero(region_data[r].to_array().sel(latitude=row['latitude'], longitude=row['longitude']).stack(time_var = ('time', 'variable')).dropna(dim='time_var', how='all').values):
                        indexes_to_drop.append(index)
                tmp_df.drop(indexes_to_drop, axis=0, inplace=True)
                tmp_df[self.region_col] = r
                lat_lon_union = pd.concat([lat_lon_union, tmp_df])

                #cache the data
                lat_lon_union.to_csv()
        else:
            #load the cached data
            lat_lon_union = pd.read_csv(self.processed_path + 'lat_lon_union.csv',float_precision='round_trip')
        #join in with the labels so we have a label per lat/lon pair
        lat_lon_union = lat_lon_union.set_index(self.region_col, drop=False).join(self.labels.set_index(self.region_col, drop=False), how='left', lsuffix='left', rsuffix='right')

        #define the split between train and test
        date_min = np.datetime64(self.date_start)
        date_max = np.datetime64(self.date_end)
        train_date_cutoff = np.datetime64(self.date_train_test_cutoff)

        #split the train/test data
        labels_data_union = lat_lon_union[lat_lon_union[self.parsed_date_col] >= date_min]
        labels_data_union = labels_data_union[labels_data_union[self.parsed_date_col] <= date_max]
        #copy so we can delete the overall data and only keep the filtered
        labels_data_train = labels_data_union[labels_data_union[self.parsed_date_col] <= train_date_cutoff].copy()
        labels_data_test = labels_data_union[labels_data_union[self.parsed_date_col] > train_date_cutoff].copy()
        labels_data_train.reset_index(inplace=True)
        labels_data_test.reset_index(inplace=True)

        return labels_data_train, labels_data_test


    def get_data_zarr(self, region, lat, lon, lookback_days, date):
        """
        utility to get data for a specific point

        Keyword Arguments
        region: the region the point exists in
        lat: the latitude of the point to lookup
        lon: the longitude of the point to lookup
        lookback_days: the number of days prior to the date to also return
        date: the date which marks the end of the dataset (same date as the desired label)
        """
        #print(region + ' ' + str(lat) + ', ' + str(lon) + ' ' + str(date))
        state = self.get_state_for_region(region)
        earliest_data, season = PrepML.date_to_season(date)

        path = self.processed_path + '/' + season + '/' + state + '/Region_' + region + '.zarr'
        #print('*Opening file ' + path)

        tmp_ds = xr.open_zarr(path, consolidated=True)
        start_day = date - np.timedelta64(lookback_days-1, 'D')
        #print('start day ' + str(start_day))
        tmp_ds = tmp_ds.sel(latitude=lat, longitude=lon, method='nearest').sel(time=slice(start_day, date))

        date_values_pd = pd.date_range(start_day, periods=lookback_days, freq='D')
        #reindex should fill missing values with NA
        tmp_ds = tmp_ds.reindex({'time': date_values_pd})

        tmp_ds = tmp_ds.reset_index(dims_or_levels='time', drop=True).load()
        return tmp_ds


    def process_sample(self, iter_tuple, lookback_days):
        """
        Convienience method to take a tuple and pull the data for it from the zarr files

        Keyword Arguments
        iter_tuple:
        lookback_days: the number of days prior to the date to also return
        """
        row = iter_tuple[1]
        d = row[self.parsed_date_col]

        lat = row['latitude']
        lon = row['longitude']
        reg = row[self.region_col]
        #print('region: ' + reg + ' date ' + str(d))
        ds = self.get_data_zarr(reg, lat, lon, lookback_days, d)

        #print("actual data")
        if ds.time.shape[0] != lookback_days:
            print(ds)
            print('Need to drop! Error, incorrect shape ' + str(ds.time.shape[0]) + ' on time ' + str(d))
        return (ds)


    def get_xr_batch(self, labels, lookback_days=14, batch_size=64, y_column='Day1DangerAboveTreeline', label_values=['Low', 'Moderate', 'Considerable', 'High'], oversample={'Low':True, 'Moderate':False, 'Considerable':False, 'High':True}, random_state=1, n_jobs=-1):
        """
        Primary method to take a set of labels and pull the data for it
        the data is large so generally this needs to be done it batches
        and then stored on disk
        For a set of labels and a target column from the labels set create the ML data

        Keyword Arguments
        labels: the set of labels we will randomly choose from
        lookback_days: the number of days prior to the date in the label to also return which defines the timeseries (default: 14)
        batch_size: the size of the data batch to return (default: 64)
        y_column: the column in the label set to use as the label (default: Day1DangerAboveTreeline)
        label_values: possible values for the y label (default: ['Low', 'Moderate', 'Considerable', 'High'])
        oversample: dictionary defining which labels from the label_values set to apply naive oversampling to (default: {'Low':True, 'Moderate':False, 'Considerable':False, 'High':True})
        random_state: define a state to force datasets to be returned in a reproducable fashion (deafault: 1)
        n_jobs: number of processes to use (default: -1)
        """

        labels_data = labels

        X = None
        y = None

        first = True
        first_y = True
        num_in_place = 0
        error_files = []
        while num_in_place < batch_size:
            if not first:
                #if we didn't meet the full batch size
                #continue appending until its full
                #if num_in_place % 5 == 0:
                print('Filling remaining have ' + str(num_in_place))
                sample_size = batch_size-num_in_place
                if sample_size < len(label_values):
                    sample_size = len(label_values)
            else:
                sample_size = batch_size

            batch_lookups = []
            for l in label_values:
                print('    on label: ' + l + ' with samplesize: ' + str(int(sample_size/len(label_values))))
                print('    len: ' + str(len(labels_data[labels_data[y_column]==l])))
                label_slice = labels_data[labels_data[y_column]==l]
                size = int(sample_size/len(label_values))
                #ensure the propose sample is larger than the available values
                if len(label_slice) < size:
                    size = len(label_slice)
                if size > 0:
                    batch_lookups.append(label_slice.sample(size, random_state=random_state))

                    if not oversample[l]:
                        labels_data = labels_data.drop(batch_lookups[-1].index, axis=0)



            #sample frac=1 causes the data to be shuffled
            batch_lookup = pd.concat(batch_lookups).sample(frac=1)
            #print('lookup shape: ' + str(batch_lookup.shape))
            batch_lookup.reset_index(inplace=True, drop=True)

            func = partial(self.process_sample, lookback_days=lookback_days)
            data = Parallel(n_jobs=n_jobs)(map(delayed(func), batch_lookup.iterrows()))

            #print('data has len: ' + str(len(data)))
            to_delete = []
            #delete backwards so we can delete by index
            for i in reversed(range(len(data))):
                #print('on i: ' + str(i))
                if data[i] is None:
                    print('deleting ' + str(i))
                    del data[i]
                    batch_lookup = batch_lookup.drop(i, axis=0)


            for d in sorted(to_delete, reverse=True):
                print('deleting ' + str(d))
                del data[d]

            for f in data:
                if f is None:
                    print('Still have none in data')

            if first and len(data) > 0:
                X = xr.concat(data, dim='sample')
                y = batch_lookup
                first = False
            elif not first and len(data) > 0:
                X_t = xr.concat(data, dim='sample')
                X = xr.concat([X, X_t], dim='sample')#, coords='all', compat='override')
                y = pd.concat([y, batch_lookup], axis=0)

            num_in_place = y.shape[0]
            #print('Num: ' + str(num_in_place))

        y = y.reset_index(drop=True)
        X = X.reindex({'sample': y.apply(lambda r: str(r[self.parsed_date_col]) + ': ' + r[self.region_col], axis=1)})
        return X, y, labels_data

    @staticmethod
    def prepare_batch_simple(X, y):
        """
        ensure, X and y indexes are aligned

        Keyword Arguments
        X: The X dataframe
        y: the y dataframe
        """

        X = X.sortby(['sample', 'latitude', 'longitude'])

        sample = y.apply(lambda row: '{}: {}'.format(row['parsed_date'], row['UnifiedRegion']), axis=1)
        y['sample'] = sample
        y = y.set_index(['sample', 'latitude', 'longitude'])
        y.sort_index(inplace=True)
        y.reset_index(drop=False, inplace=True)
        return X, y


    def cache_batches(self, labels, batch_size=64, total_rows=6400, train_or_test='train', lookback_days=14, n_jobs=14):
        """
        method to enable batches to be generated based on total amount of data as well as batch size
        batches stores as zarr & parquet

        Keyword Arguments
        labels: the set of labels to choose from
        batch_size: the number of samples to cache in a single batch (default: 64)
        total_rows: the total number of rows to cache made up of multiple batches (default: 6400)
        train_or_test: is this a train or test set--used in the file label (default: train)
        lookback_days: number of days prior to the label date to include in the timeseries (default: 14)
        n_jobs: number of processes to use (default: 14)

        Returns: remaining labels (labels which weren't used in the dataset creation)
        """
        remaining_labels = labels
        for i in range(0, total_rows, batch_size):
            print(str(datetime.datetime.now()) + ' On ' + str(i) + ' of ' + str(total_rows))
            X, y, remaining_labels = self.get_xr_batch(remaining_labels, lookback_days=lookback_days, batch_size=batch_size, n_jobs=n_jobs)
            X.to_zarr(self.ml_path + 'X_' + train_or_test + '_' + str(i/batch_size) + '.zarr')
            y.to_parquet(self.ml_path + 'y_' + train_or_test + '_' + str(i/batch_size) + '.parquet')
        return remaining_labels


    def cache_batches_np(self,
                         labels,
                         batch_size=50,
                         total_rows=10000,
                         train_or_test='train',
                         lookback_days=180,
                         y_column='Day1DangerAboveTreeline',
                         label_values=['Low', 'Moderate', 'Considerable', 'High'],
                         oversample={'Low':True, 'Moderate':False, 'Considerable':False, 'High':True},
                         n_jobs=14):
        """
        method to enable batches to be generated based on total amount of data as well as batch size
        batches returned for further processing

        Keyword Arguments
        labels: the set of labels to choose from
        batch_size: the number of samples to cache in a single batch (default: 64)
        total_rows: the total number of rows to cache made up of multiple batches (default: 6400)
        train_or_test: is this a train or test set--used in the file label (default: train)
        lookback_days: number of days prior to the label date to include in the timeseries (default: 14)
        y_column: the column in the label set to use as the label (default: Day1DangerAboveTreeline)
        label_values: possible values for the y label (default: ['Low', 'Moderate', 'Considerable', 'High'])
        oversample: dictionary defining which labels from the label_values set to apply naive oversampling to (default: {'Low':True, 'Moderate':False, 'Considerable':False, 'High':True})
        n_jobs: number of processes to use (default: 14)

        Returns: tuple containing the batch *X,y) and remaining labels (labels which weren't used in the dataset creation)
        """
        remaining_labels = labels
        for i in range(0, total_rows, batch_size):
            print(str(datetime.datetime.now()) + ' *On ' + str(i) + ' of ' + str(total_rows))
            X, y, remaining_labels = self.get_xr_batch(remaining_labels, lookback_days=lookback_days, batch_size=batch_size, y_column=y_column, n_jobs=n_jobs)

        return PrepML.prepare_batch_simple(X, y), remaining_labels

    #TODO: derive num_variables and lookback_days from the input set
    #TODO: only write out one y file per X file
    def create_memmapped(self, remaining_labels, train_or_test = 'train', num_variables=1131, num_rows = 10000, lookback_days=180, batch=0, batch_size=500):
        """
        Generate a set of batches and store them in a memmapped numpy array
        this is the technique used to prep data for timeseriesai notebook
        Will store a single numpy X file in the ML directory as well as several y parquet files (one per batch size)
        Keyword Arguments
        remaining_labels: the set of labels to draw from
        train_or_test: is this a train or test set--used in the file label (default: train)
        num_variables: number of variables in the X set (default: 1131)
        num_rows: total number of rows to store in the file (deafult: 10000)
        lookback_days: number of days before the label date to include in the timeseries (default: 180)
        batch: batch number to start in (default: 0) used in case you are generating multiple files
        batch_size: number of rows to process at once to accomodate memory limitations (default: 500)
        """

        # Save a small empty array
        X_temp_fn = self.ml_path + '/temp_X.npy'
        np.save(X_temp_fn, np.empty(1))

        # Create a np.memmap with desired dtypes and shape of the large array you want to save.
        # It's just a placeholder that doesn't contain any data
        X_fn = self.ml_path + '/X' + train_or_test + '_batch_' + str(batch) + '_on_disk.npy'

        X = np.memmap(X_temp_fn, dtype='float32', shape=(num_rows, num_variables, lookback_days))

        # We are going to create a loop to fill in the np.memmap
        start = 0
        for i in range(0, num_rows, batch_size):
            print('On ' + str(i) + ' of ' + str(num_rows))
            # You now grab a chunk of your data that fits in memory
            # This could come from a pandas dataframe for example
            dfs, remaining_labels = self.cache_batches_np(remaining_labels, batch_size=batch_size, total_rows=500)
            #need to make sure all the variables are in the same order (there was an issue that they weren't between train and test sets)
            X_df = dfs[0].sortby('variable')
            y_df = dfs[1]
            end = start + batch_size

            # I now fill a slice of the np.memmap
            X[start:end] = X_df.vars.values[:batch_size] #sometimes the process will add a few extras, filter them

            #just save y as parquet
            y_df[:batch_size].to_parquet(self.ml_path + '/y_' + train_or_test + '_batch_' + str(batch) + '_' + str(i/batch_size) + '.parquet')
            start = end
            del X_df, y_df

        #I can now remove the temp file I created
        os.remove(X_temp_fn)

        # Once the data is loaded on the np.memmap, I save it as a normal np.array
        np.save(X_fn, X)
        return remaining_labels


    def concat_memapped(self, to_concat_filenames, dim_1_size=1131, dim_2_size=180):
        """
        concat multiple numpy files on disk in to a single file
        required for timeseriesai notebook as input to that is a single memmapped file containing X train and test data

        Keyword Arguments:
        to_concat_filenames: the files to concat
        dim_1_size: number of variables in the files (default: 1131)
        dim_2_size: number of lookback dates in the files (length of timeseries) (default: 180)
        """
        to_concat = []
        for i in range(len(to_concat_filenames)):
            to_concat.append(np.load(to_concat_filenames[i], mmap_mode='r'))

        dim_0_size = 0

        for i in range(len(to_concat)):
            dim_0_size += to_concat[i].shape[0]
            assert(to_concat[i].shape[1] == dim_1_size)
            assert(to_concat[i].shape[2] == dim_2_size)

        X_temp_fn = self.ml_path + '/temp_X.npy'
        np.save(X_temp_fn, np.empty(1))
        X_fn = self.ml_path + '/X_all.npy'
        X = np.memmap(X_temp_fn, dtype='float32', shape=(dim_0_size, dim_1_size, dim_2_size))
        dim_0_start = 0
        for i in range(len(to_concat)):
            print('On file ' + str(i) + ' of ' + str(len(to_concat)))
            dim_0 = to_concat[i].shape[0]
            X[dim_0_start:dim_0_start+dim_0] = to_concat[i]
            dim_0_start += dim_0


        #I can now remove the temp file I created
        os.remove(X_temp_fn)

        # Once the data is loaded on the np.memmap, I save it as a normal np.array
        np.save(X_fn, X)
        del to_concat

    #TODO: add the ability to restart from a cached label file
    def generate_train_test_local(self,
                                  train_labels,
                                  test_labels,
                                  num_train_files=1,
                                  num_test_files=1,
                                  num_train_rows_per_file=10000,
                                  num_test_rows_per_file=500,
                                  num_variables=1131):
        """
        create several memapped files
        we do this as the technique to create one has some memory limitations
        also due to the memory limitations sometimes this process runs out of memory and crashes
        which is why we cache the label state after every iteration so we can restart at that state
        15 mins for 10000 rows using all 16 cores on my machine
        I can generate a max of ~50000 rows per batch with 48 gb of ram before running out of memory
        """

        #get a sample so we can dump the feature labels
        X, _, _ = self.get_xr_batch(train_labels, lookback_days=7, batch_size=4)
        pd.Series(X.variable.data).to_csv(self.ml_path + '/FeatureLabels.csv')

        filenames = []
        for i in range(0, num_train_files):
            remaining_labels_train = self.create_memmapped(train_labels, train_or_test = 'train', num_variables=num_variables, num_rows=num_train_rows_per_file, batch=i)
            filenames.append(self.ml_path + '/Xtrain_batch_' + str(i) + '_on_disk.npy')
            #with open(ml_path + 'remaining_labels_train.p', 'wb' ) as file:
            #    pickle.dump(remaining_labels_train, file)


        #same process for test
        for i in range(0, num_test_files):
            remaining_labels_test = self.create_memmapped(test_labels, train_or_test = 'test', num_variables=num_variables, num_rows=num_test_rows_per_file, batch=i)
            filenames.append(self.ml_path + '/Xtest_batch_' + str(i) + '_on_disk.npy')
            #with open(ml_path + 'remaining_labels_test.p', 'wb' ) as file:
            #    pickle.dump(remaining_labels_test, file)

        self.concat_memapped(filenames, num_variables)

        return remaining_labels_train, remaining_labels_test

