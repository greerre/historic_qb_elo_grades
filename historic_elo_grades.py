import pandas as pd
import numpy
import requests

## output location ##
output_folder = '/Users/robertgreer/Documents/Coding/NFL/Insights/QB Grades'

## pull data ##
data_link = 'https://projects.fivethirtyeight.com/nfl-api/nfl_elo.csv'
data_df = pd.read_csv(data_link)

## only want data w/ QB grades ##
data_df = data_df[(~numpy.isnan(data_df['qbelo1_pre'])) & (~numpy.isnan(data_df['qbelo2_pre']))]

## excluding playoffs ##
data_df = data_df[(~numpy.isnan(data_df['playoff']))]


## create weeks from dates ##
## these will be yearly weeks, not season weeks ##
data_df['date_time'] = pd.to_datetime(data_df['date'])

## mondays are new weeks, so subtract a day and then trunc ##
data_df['date_time'] = data_df['date_time'] - pd.Timedelta(days=1)
data_df['week_of'] = data_df['date_time'].dt.week

## create a flat file ##
home_data_df = data_df.copy()[[
    'season',
    'week_of',
    'qb1',
    'qb1_value_post',
    'score1',
    'score2'
]].rename(columns={
    'qb1' : 'qb_name',
    'qb1_value_post' : 'qb_elo_value',
    'score1' : 'points_for',
    'score2' : 'points_against',
})

away_data_df = data_df.copy()[[
    'season',
    'week_of',
    'qb2',
    'qb2_value_post',
    'score2',
    'score1'
]].rename(columns={
    'qb2' : 'qb_name',
    'qb2_value_post' : 'qb_elo_value',
    'score2' : 'points_for',
    'score1' : 'points_against',
})

flat_df = pd.concat([home_data_df,away_data_df])
flat_df = flat_df.sort_values(by=['season','week_of'])

## add some stats ##
flat_df['point_margin'] = flat_df['points_for'] - flat_df['points_against']
flat_df['win'] = numpy.where(flat_df['point_margin'] > 0,1,0)

## calculate median and era adjustment ##
median_df = flat_df.groupby(['season','week_of'])['qb_elo_value'].median().reset_index().rename(columns={
    'qb_elo_value' : 'median_qb_elo_value',
})
flat_df = pd.merge(flat_df,median_df,on=['season','week_of'],how='left')
flat_df['qb_elo_value_era_adjusted'] = flat_df['qb_elo_value'] - flat_df['median_qb_elo_value']

## add a cumulative game count ##
flat_df['game_number'] = flat_df.groupby(['qb_name']).cumcount() + 1

## add ranking ##
flat_df['qb_rank'] = flat_df.groupby(['season','week_of'])['qb_elo_value'].rank(method='max', ascending=False)
flat_df['top_1_qb'] = numpy.where(flat_df['qb_rank']<=1, 1,0)
flat_df['top_3_qb'] = numpy.where(flat_df['qb_rank']<=3, 1,0)
flat_df['top_5_qb'] = numpy.where(flat_df['qb_rank']<=5, 1,0)

## export flat file ##
flat_df = flat_df.sort_values(by=['qb_name','game_number'])
flat_df.to_csv('{0}/qb_all_games.csv'.format(output_folder))

## aggregate careers ##
agg_dict = {
    'game_number' : 'max',
    'qb_elo_value_era_adjusted' : 'sum',
    'qb_elo_value_era_adjusted' : 'mean',
    'win' : 'mean',
    'top_1_qb' : 'mean',
    'top_3_qb' : 'mean',
    'top_5_qb' : 'mean',
}

agg_df = flat_df.groupby('qb_name').agg(agg_dict).reset_index()
agg_df = agg_df.rename({

})
