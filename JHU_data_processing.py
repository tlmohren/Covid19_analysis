import pandas as pd 
import matplotlib.dates as mdates  
import numpy as np
from datetime import timedelta  
import matplotlib.dates as dt      
import glob


state_dict = {
        'AK': 'Alaska',
        'AL': 'Alabama',
        'AR': 'Arkansas',
        'AS': 'American Samoa',
        'AZ': 'Arizona',
        'CA': 'California',
        'CO': 'Colorado',
        'CT': 'Connecticut',
        'DC': 'District of Columbia',
        'DE': 'Delaware',
        'FL': 'Florida',
        'GA': 'Georgia',
        'GU': 'Guam',
        'HI': 'Hawaii',
        'IA': 'Iowa',
        'ID': 'Idaho',
        'IL': 'Illinois',
        'IN': 'Indiana',
        'KS': 'Kansas',
        'KY': 'Kentucky',
        'LA': 'Louisiana',
        'MA': 'Massachusetts',
        'MD': 'Maryland',
        'ME': 'Maine',
        'MI': 'Michigan',
        'MN': 'Minnesota',
        'MO': 'Missouri',
        'MP': 'Northern Mariana Islands',
        'MS': 'Mississippi',
        'MT': 'Montana',
        'NA': 'National',
        'NC': 'North Carolina',
        'ND': 'North Dakota',
        'NE': 'Nebraska',
        'NH': 'New Hampshire',
        'NJ': 'New Jersey',
        'NM': 'New Mexico',
        'NV': 'Nevada',
        'NY': 'New York',
        'OH': 'Ohio',
        'OK': 'Oklahoma',
        'OR': 'Oregon',
        'PA': 'Pennsylvania',
        'PR': 'Puerto Rico',
        'RI': 'Rhode Island',
        'SC': 'South Carolina',
        'SD': 'South Dakota',
        'TN': 'Tennessee',
        'TX': 'Texas',
        'UT': 'Utah',
        'VA': 'Virginia',
        'VI': 'Virgin Islands',
        'VT': 'Vermont',
        'WA': 'Washington',
        'WI': 'Wisconsin',
        'WV': 'West Virginia',
        'WY': 'Wyoming'
}



def replace_state( x):
    
    error_dict = {'Chicago':'Illinois',
            'NE (From Diamond Princess)':'Nebraska',
            'CA (From Diamond Princess)':'California',
            'TX (From Diamond Princess)':'Texas',
            'Unassigned Location (From Diamond Princess)':'Other',
            'D.C.':'District of Columbia',
            'Puerto Rico':'Other',
            'Guam':'Other',
            'U.S.':'Other',
            'US':'Other',
            'Virgin Islands':'Other',
            'United States Virgin Islands':'Other',
            'Wuhan Evacuee':'Other',
            'American Samoa':'Other',
            'Northern Mariana Islands':'Other', 
            'OR ':'Oregon'} 
    
    state_entry = x['Province/State'].split(", ")[-1] 
    if state_entry in  state_dict.keys(): 
        new =  state_dict[ state_entry]  
    elif state_entry in error_dict.keys():
        new = error_dict[state_entry]  
    else:
        new = state_entry   
    return new 


def load_daily_reports( file_path):
    
    daily_reports = glob.glob(file_path + '\*.csv') 
    df = pd.DataFrame()
    for file in daily_reports :
        df_temp = pd.read_csv( file, index_col=None, header=0)  

        if  '03-13-2020' in file :
            # correct for mistake in JHU data set
            df_temp['Last Update'] = pd.to_datetime(df_temp['Last Update']   )
            df_temp['Last Update'] = df_temp['Last Update'] + timedelta(days=2)  

        if  '03-09-2020' in file : 
            # correct for mistake in JHU data set
            df_temp['Last Update'] = pd.to_datetime(df_temp['Last Update']   )
            df_temp['Last Update'] = df_temp['Last Update'] + timedelta(days=1) 

        df = df.append(df_temp, sort=True)  
    return df


def process_daily_data( df_daily):
    # convert both separately 
    df_daily['Last Update'] = pd.to_datetime(df_daily['Last Update']   )
    df_daily['Last_Update'] = pd.to_datetime(df_daily['Last_Update']   )   # 
    cond = df_daily['Last_Update'].isnull()
    df_daily['Last Update'] = df_daily['Last Update'].where(cond, df_daily['Last_Update'] ) 
    df_daily['Datetime'] = pd.to_datetime(df_daily['Last Update'] , unit='D'   ) 

    ### optional: convert times to pacific time 
    df_daily['Date'] = df_daily['Datetime'].dt.date 

    # compensate country/region
    df_daily['Country/Region'].isnull().sum() 
    cond = df_daily['Country_Region'].isnull()
    df_daily['Country/Region'] = df_daily['Country/Region'].where(cond, df_daily['Country_Region'] ) 

    # province state
    cond = df_daily['Province_State'].isnull()
    df_daily['Province/State'] = df_daily['Province/State'].where(cond, df_daily['Province_State'] ) 


    col_order = ['Date','Country/Region','Province/State','Active','Confirmed','Deaths','Recovered' ]
    df_daily = df_daily[col_order]
    
    bool_US = df_daily['Country/Region'] =='US'
    df_US = df_daily[bool_US ]

    df_US.loc[:,'State'] = df_US.copy().apply( replace_state, axis=1)
    
    df_state =  df_US.groupby(['State','Date']).sum().reset_index()
  
    df_state = df_state.sort_values(by=['State','Date'], ascending=True )  
    df_state.head() 
 
    # drop some states
    bool_other = df_state['State'].str.contains( 'Other' , regex=False) 
    df_state.drop( df_state[bool_other].index, inplace=True)  
  
    bool_other = df_state['State'].str.contains( 'Princess' , regex=False) 
    df_state.drop( df_state[bool_other].index, inplace=True)  

    return df_state 


def merge_countrydf(path, file_list):
    
    df_list = []
    for file in file_list: 
        df_list.append( pd.read_csv( path + file , index_col=None, header=0) )
        
    df = pd.DataFrame()
    date_cols = df_list[0].columns[  4:  ]

    # for date_col in date_cols[:]: 
    for i in range(len(date_cols)) : 
        col_index = df_list[0].columns[ [1 ] ].append( date_cols[[i]] ) 
        df_temp = df_list[0][col_index].copy() 
        df_temp[ 'Death'] = df_list[1][date_cols[[i]] ]  
        df_temp[ 'Recovered'] = df_list[2][date_cols[[i]] ]  # works but gives warning  
        df_temp['Date'] = date_cols[i]
        df_temp = df_temp.rename( columns={date_cols[i]:'Confirmed'})    
        df = df.append(df_temp)     
        
    df = df.groupby(['Country/Region','Date']).sum().reset_index()
    
    df['Date'] = pd.to_datetime( df['Date'] ).dt.date 
        
    df = df.sort_values( by=['Country/Region','Date']).reset_index(drop=True) 

    return df
 

def days_since_threshold( date_series, value_series, region_series, threshold_val ) : 
    
    # find all that belong to last day
    last_day = date_series.max() 
     
    # find unique entries: 
    countries = region_series.unique() 
        
    # initialize new column
    newday_col = pd.Series(np.nan, index= region_series.index ) 
    
    for country in countries : 
         
        bool_country = (region_series == country).values
        
        x = date_series[bool_country] 
        y = value_series[bool_country]  
        
        bool_threshold_cases = (y >= threshold_val)
                                           
        # if any time the cases reach above threshold
        if bool_threshold_cases.sum() > 0: 
            day0 = x[bool_threshold_cases].iloc[0] 
        else: 
            day0 = last_day + timedelta(days=1) 

        newdays = ( x - day0).dt.days   
        newday_col[bool_country] =  newdays.values
          
    return newday_col  


def get_exponential_ratio( date_series, value_series, region_series, averaging_period ): 
 
    last_day = date_series.max() 
    prior_day = date_series.max() - timedelta(days=averaging_period)
    bool_last = date_series == last_day
    bool_prior = date_series == prior_day

    new_ratio_col = pd.Series(np.nan, index= region_series.index  ) 

    countries =  region_series.unique()
    for country in countries: 
        bool_country =  region_series == country   
        
        if value_series.loc[bool_last & bool_country ].values[0] == 0:
            ratio = 0
        elif value_series.loc[bool_prior & bool_country ].values[0] == 0:
            ratio = np.inf
        else:
            ratio = value_series.loc[bool_last & bool_country ].values[0]  / \
                    value_series.loc[bool_prior & bool_country ].values[0]  
        daily_ratio = ratio**(1/averaging_period)   
        new_ratio_col[bool_country] =  daily_ratio
        
    return new_ratio_col


def add_measures_column( fileName, date_series, region_series ):

	measures_col = pd.Series(np.nan, index= region_series.index  ) 

	df_m = pd.read_csv( fileName, index_col=None ) 
	df_m['Date'] = pd.to_datetime( df_m['Date'] ).dt.date 

	# add measures to additional column
	for i,row in df_m.iterrows(): 
		if  'Country/Region' in  df_m.columns.tolist():
			country = row['Country/Region']
		elif 'State' in  df_m.columns.tolist():
			country = row['State']
		date = row['Date']
		bool_loc = ( region_series == country) & ( date_series == date) 
		measures_col.loc[bool_loc] = row['Measure']
	return measures_col



def find_daily_cases( date_series, value_series):
    daily_col = pd.Series(np.nan, index= value_series.index  ) 
    days = date_series.unique()   
    
    bool_day0 = date_series == days[0]
    daily_col.loc[bool_day0 ] = 0 

    for day in days[1:]:      

        bool_day = date_series == day 
        bool_prior = date_series == ( day- timedelta(days=1))  

        delta = value_series[bool_day].values - value_series[bool_prior].values
        
        daily_col[bool_day] = delta 
    return daily_col

