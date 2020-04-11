import pandas as pd
import matplotlib.pyplot as plt 
import matplotlib.dates as mdates  
import numpy as np
from datetime import timedelta
from matplotlib.dates import date2num       #-->Update 
from matplotlib.colors import ListedColormap
import json
import matplotlib.dates as dt    
import geopandas as gpd
import datetime
# import geopandas as gpd
import shapely.affinity as shp
import glob

####--------------------parameters --------------------------------------
plot_country = True
plot_states = True
save_fig = True
show_plot = False

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

# figure size
full_w = (12,7)
half_w = (6,4) 

cols = np.array([[213,62,79],
[244,109,67],
[253,174,97],
[254,224,139], 
[171,221,164], 
[50,136,189]]) /255 
cols = np.flipud(cols)
cmap = ListedColormap(cols) 

threshold_cases = 100
threshold_deaths = 25

# ticks 
tick_list = [1e2,2e2,5e2,1e3,2e3,5e3,1e4,2e4,5e4,1e5,2e5,5e5,1e6,2e6,5e6,]
tick_label_list = [100,200,500, 1000,2000,5000, '10k','20k','50k', '100k','200k','500k','1m','2m','5m']

# doubling rate average period 
averaging_period = 3

# china artificial days since day 0, next + china_ad
china_add = 6

# annotation properties of figures
bbox_props = dict(boxstyle="round,pad=0.1", fc="w", ec="w", lw=2, alpha = 0.5)

notable_countries = ['US','Italy','Spain','China', 'France','Germany','Iran',
                     'United Kingdom','Switzerland','Turkey','Netherlands','Austria',
                        'Korea, South','Brazil'  ,'Sweden','Japan',
                        'Dominican Republic', 'Russia','Ukraine' ]

 	# compute doubling rate 
bin_array = np.array( [-1, 2.**(1./20), 2.**(1./15), 2.**(1./10), 2.**(1./7), 2.**(1./5)  ,np.inf ]) 
bin_labels = ['20','15','10','7','5' ]

dot_col = np.ones((3))*0.8 
emph_col = [0.5,0.5,0.5] 
# goal_col = "#e74c3c"
goal_col = "r"
dot_alpha = 1 



####------------------functions-- --------------------------------------
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


####------------------compute days since threshold-------------------------------------
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
        # print(days[0] , day- timedelta(days=1))

        bool_day = date_series == day 
        bool_prior = date_series == ( day- timedelta(days=1))  

        delta = value_series[bool_day].values - value_series[bool_prior].values
        
        daily_col[bool_day] = delta 
    return daily_col





def smooth(x,window_len=11,window='hanning'):
  
    # ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']
    s=np.r_[x[window_len-1:0:-1],x,x[-2:-window_len-1:-1]]
    #print(len(s))
    if window == 'flat': #moving average
        w=np.ones(window_len,'d')
    else:
        w=eval('np.'+window+'(window_len)')

    y=np.convolve(w/w.sum(),s,mode='valid')
    return y  


def plot_highlight( ax_p, goal_country, date_series, value_series, region_series, 
	countries_to_highlight): 
    xCmax = date_series.max() 
    yCmax = value_series.max() 
 
    bool_value = value_series > threshold_cases 
    threshold_countries = region_series[bool_value].unique()

    for country in threshold_countries:  
        bool_country = region_series == country 

        x_sub = date_series[bool_country]
        y_sub = value_series[bool_country]
             
        if country == goal_country: 
            ax_p.plot( x_sub,  y_sub ,'-' ,
                    ms=3,lw=2.5, label=country, 
                    color=goal_col ,alpha = dot_alpha)      
            
            ax_p.scatter( x_sub.iloc[-1],  y_sub.iloc[-1], 100, goal_col,
                         edgecolors='w',zorder = 5, linewidths=2)
            ax_p.annotate( country ,[3,yCmax*1.2], color=goal_col, fontsize = 10,zorder = 5 )
            
        elif country in countries_to_highlight: 
            ax_p.plot( x_sub, y_sub,'-' ,
                    ms=3,lw=1.5, label=country, 
                    color=emph_col ,zorder = 2 ) 
            ax_p.plot( x_sub.iloc[-1],  y_sub.iloc[-1], marker='.',
                      markersize=10, markerfacecolor=emph_col , 
                    markeredgecolor='w',markeredgewidth=1,zorder =3 ) 
        else: 
            ax_p.plot( x_sub,  y_sub,'-' ,
                    ms=3,lw=.5, label=country, 
                    color=dot_col ,alpha = dot_alpha,zorder = 1) 
             
    ax_p.set_yscale('log')  
    ax_p.yaxis.set_ticks([1e2, 1e3,1e4,1e5,1e6])
    ax_p.yaxis.set_ticklabels(['100','1k','10k','100k','1M']) 

    ax_p.spines['top'].set_visible(False)
    ax_p.spines['right'].set_visible(False)
    
    return ax_p 



def plot_daily( ax_p, date_col, data_series, measures = pd.DataFrame() ):
    
    # plotting parameters 
    bar_alpha = .15
    fill_alpha = .2 
    
    bar_col = 'k'#np.array([ 1,1,1] )*0.5
    fill_col = 'r'
    bar_line = 'k'
    fill_line = 'r' 

    filter_w = 9
    filter_w_delay = 13

    case_delay = 12
    death_delay = 12

    edge_cut = int( np.floor(filter_w/2) ) 
    edge_cut_delay = int( np.floor(filter_w_delay/2) )  
    
    weeks = mdates.DayLocator(bymonthday=[1,11,21], interval=1, tz=None)
    months_fmt = mdates.DateFormatter('%m-%d') 
    #------------------------------------------------------
 
    days=  date_col.unique()

    date_col = date_col.apply(date2num) 
    
    z_bar= 3
    z_fill = 1
    
    # smoothen data
    plot_data =  data_series.values  
    plot_data_fake = np.append( plot_data, plot_data[-1]*np.ones((2)) )
    plot_smooth = smooth( plot_data_fake ,filter_w,'hamming' )[edge_cut:-edge_cut-2]
    plot_smooth_delay = smooth( plot_data_fake ,filter_w_delay,'hamming' )[edge_cut_delay:-edge_cut_delay-2]
    
    # plot data
    ax_p.bar( date_col,  plot_data   ,
             alpha = bar_alpha , color=bar_col, 
                label = 'Reported cases', zorder = z_bar) 
    ax_p.plot( date_col, plot_smooth, color=bar_line, zorder = z_bar)
    
    ax_p.plot( date_col.iloc[0:-case_delay] , plot_smooth_delay[case_delay:] , color=fill_line, zorder = z_fill)
    ax_p.fill_between( date_col.iloc[0:-case_delay] , 0, plot_smooth_delay[case_delay:] ,
                      alpha= fill_alpha, color=fill_col, 
                      label='12-day delay', zorder = z_fill
                    )

    # axis modify
    ax_p.xaxis_date()
    ax_p.xaxis.set_major_locator(weeks)
    ax_p.xaxis.set_major_formatter(months_fmt)  
 
    cmax = plot_smooth.max()*1.2  
    ax_p.set_ylim([0,cmax])  
    
    arrowprops = dict(    arrowstyle = "->"    )
 
    # annotate
    counter = 0
    for i,row in measures.iterrows(): 
        ax_p.plot( [row['Date'],row['Date']] ,[0,cmax],'--', alpha = 0.5,color='k',linewidth=1,zorder  = 6)  
        chinese = ['Hubei','China'] 
        if any(c in measures.iloc[0,:]['Measure'] for c in chinese):
            ax_p.annotate( row['Measure'], (row["Date"],cmax*(0.94-0.1*counter)) ,
                              xytext = ( days[-1],cmax*(0.9-0.1*counter)) ,
                             rotation = 0, va='bottom',ha='right',fontsize=10, arrowprops=arrowprops)   
        else:
            ax_p.annotate( row['Measure'], (row["Date"],cmax*(0.94-0.1*counter)) ,
                              xytext = ( days[0],cmax*(0.9-0.1*counter)) ,
                             rotation = 0, va='bottom',ha='left',fontsize=10, arrowprops=arrowprops)    
        counter = counter+1 
    return ax_p 

	    
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



    df_US.loc[:,'State'] = df_US.copy().apply(replace_state, axis=1)
    
    
    df_state =  df_US.groupby(['State','Date']).sum().reset_index()
  
    df_state = df_state.sort_values(by=['State','Date'], ascending=True )  
    df_state.head() 
 
    # drop some states
    bool_other = df_state['State'].str.contains( 'Other' , regex=False) 
    df_state.drop( df_state[bool_other].index, inplace=True)  
  
    bool_other = df_state['State'].str.contains( 'Princess' , regex=False) 
    df_state.drop( df_state[bool_other].index, inplace=True)  


    return df_state 





# ####------------------run plotting script--------------------------------------
if __name__ == '__main__':
	print('run script directly') 


	# ---------------------------------------------------------
	# --------------merge and data processing------------------
	# ---------------------------------------------------------

	path = r'D:\Code_projects\Covid19_analysis\COVID-19\csse_covid_19_data\csse_covid_19_time_series'
	file_list = ['\\time_series_covid19_confirmed_global.csv',
	         '\\time_series_covid19_deaths_global.csv',
	         '\\time_series_covid19_recovered_global.csv'] 

	# merge data 
	df_country = merge_countrydf(path, file_list) 

	# remove diamond princess 
	bool_other = df_country['Country/Region'].str.contains( 'Princess' , regex=False)
	df_country.drop( df_country[bool_other].index, inplace=True) 

 	# compute delta days
	df_country['Delta C'] =  days_since_threshold( df_country['Date'],
	                                df_country['Confirmed'],
	                                df_country['Country/Region'] , 
	                                threshold_cases) 

	df_country['Delta D'] = days_since_threshold( df_country['Date'],
	                                df_country['Death'],
	                                df_country['Country/Region'] , 
	                                threshold_deaths)

	# remove days from china to make plots look better 
	bool_nochina = df_country['Country/Region']!= 'China'
	xCmax = df_country.loc[bool_nochina,'Delta C'].max()
	xDmax = df_country.loc[bool_nochina,'Delta D'].max()
	 
	last_day = df_country['Date'].unique()[-1] 

	# bool_last = df_country['Date'] == last_day 
	bool_cases= df_country['Delta C'] > (xCmax+china_add)
	bool_deaths = df_country['Delta D'] > (xDmax+china_add)
	bool_china = df_country['Country/Region'] == 'China'

	df_country.loc[bool_cases & bool_china,'Delta C'] = xCmax+ china_add
	df_country.loc[bool_deaths & bool_china,'Delta D'] = xDmax+ china_add

	# find ratio and doubling # days
	df_country['ratio'] = get_exponential_ratio( df_country['Date'], 
	                                            df_country['Confirmed'],
	                                            df_country['Country/Region'], 
	                                            averaging_period )   
	df_country['doubling'] = pd.cut( df_country['ratio'],   bin_array ,labels=range(len(bin_array)-1) , include_lowest=True )
	 
	df_country['ratioD'] = get_exponential_ratio( df_country['Date'], 
	                                            df_country['Death'],
	                                            df_country['Country/Region'], 
	                                            averaging_period )  
	df_country['doublingD'] = pd.cut( df_country['ratioD'],   bin_array ,labels=range(len(bin_array)-1) , include_lowest=True )

 
 
	df_country['Daily Confirmed'] = find_daily_cases( df_country['Date'] , df_country['Confirmed'] )
	df_country['Daily Death'] = find_daily_cases( df_country['Date'] , df_country['Death'] )
 

	df_country['Measure'] = add_measures_column( 'measures_per_country.csv', 
	                                            df_country['Date'] ,
	                                            df_country['Country/Region'])


 	#--plotting map country----------------------------
 
	world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres')) 

	countries_w = world['name'].tolist()
	countries_c = df_country['Country/Region'].unique().tolist()
	 
	conversion_dict = {'United States': 'US',
	                   'Taiwan': 'Taiwan*',
	                   'Czech Rep.':'Czechia',
	                   'Korea':'Korea, South',
	                   'Dem. Rep. Korea': 'Korea, North',
	                  'Dominican Rep.':'Dominican Republic' } 
	          
	world['name'] = world['name'].map(conversion_dict).fillna(world['name'])

	world['Cases'] = 0 
	countries = world['name'].tolist()
	 
	dates = df_country['Date'].unique() 

	for country in countries: 
	    bool_country = df_country['Country/Region'] == country 
	    bool_date = df_country['Date'] == dates[-1]
	    bool_prior = df_country['Date'] == dates[-7] 
	    if (bool_country & bool_date).sum() > 0:
	        now_cases = df_country[bool_country & bool_date ]['Confirmed'].iloc[0]
	        prior_cases = df_country[bool_country & bool_prior ]['Confirmed'].iloc[0]
	        latest_cases = (now_cases-prior_cases)/7
	    else:
	        latest_cases = 0 
	    
	    bool_world = world['name'] == country  
	    world.loc[bool_world,'Cases'] = np.log(latest_cases+1) 







	# state data import and process  
	daily_path = r'D:\Code_projects\Covid19_analysis\COVID-19\csse_covid_19_data\csse_covid_19_daily_reports'

	df_daily = load_daily_reports( daily_path )
 
	df_state = process_daily_data( df_daily ) 

	# adjust california funk 
	bool_cal = df_state['State'] == 'California'
	bool_prior = df_state['Date'] < datetime.datetime(2020,2,10).date() 
	df_state.loc[bool_cal & bool_prior,'Confirmed'] = 0 



	 # --------------------------------------------------------------------------
	# df_state add missing dates, still to turn into function 

	dates_unique =   df_state['Date'].unique()
	dates = df_country['Date'].unique()
	# dates = df_state['Date'].unique()
	state_list =  df_state['State'].unique()  
	 
	# find missing dates 
	for state in state_list:
	#     bool_state = df_state['State'] == state 
	    for date in dates:
	        bool_state = df_state['State'] == state 
	        subframe = df_state.loc[bool_state,'Date'].tolist() 
	        if date not in subframe : 
	            append_series = pd.Series({'State':state,'Date':date,'Active':0,'Confirmed':0,'Deaths':0,'Recovered':0})
	            df_state = df_state.append( append_series, ignore_index=True)
	  
	# subframe
	    bool_state = df_state['State'] == state
	    df_state[bool_state].sort_values(by=['Date'])
	 # --------------------------------------------------------------------------

	threshold_cases = 100
	threshold_deaths = 10

	df_state['Delta C'] =   days_since_threshold( df_state['Date'],
	                                df_state['Confirmed'],
	                                df_state['State'] , 
	                                threshold_cases) 

	df_state['Delta D'] =  days_since_threshold( df_state['Date'],
	                                df_state['Deaths'],
	                                df_state['State'] , 
	                                threshold_deaths)
  
	# # find ratio and doubling # days
	# averaging_period = 3

	# bin_array = np.array( [-1, 2.**(1./8), 2.**(1./7), 2.**(1./6), 2.**(1./5), 2.**(1./4) ,np.inf ]) 
	# bin_tick_labels = ['8','7','6','5','4']

	df_state['ratio'] =  get_exponential_ratio( df_state['Date'], 
	                                            df_state['Confirmed'],
	                                            df_state['State'], 
	                                            averaging_period )   
	df_state['doubling'] = pd.cut( df_state['ratio'],   bin_array ,labels=range(len(bin_array)-1) , include_lowest=True )



	df_state['ratioD'] =  get_exponential_ratio( df_state['Date'], 
	                                            df_state['Deaths'],
	                                            df_state['State'], 
	                                            averaging_period )  
	df_state['doublingD'] = pd.cut( df_state['ratioD'],   bin_array ,labels=range(len(bin_array)-1) , include_lowest=True )
 



	try_bool = df_state.groupby('State').max()['Delta C'] > 0 
	threshold_states = try_bool.index[try_bool].tolist()
 

 
	# something broken here, still to fix ------------------------------------------------

	df_state = df_state.sort_values( by=['State','Date']).reset_index(drop=True) 


	df_state['Daily Confirmed'] = find_daily_cases( df_state['Date'] , df_state['Confirmed'] )
	df_state['Daily Deaths'] = find_daily_cases( df_state['Date'] , df_state['Deaths'] )
 
	# df_state['Date']  = df_state['Date'].apply(date2num)      #-->Update

	df_state['Measure'] = add_measures_column( 'measures_per_state.csv', 
	                                            df_state['Date'] ,
	                                            df_state['State'])



  
 
	# ---------------------------------------------------------
	# --------------plotting country   ------------------------ 
	# ---------------------------------------------------------


	if plot_country:
		# -------------------log cases ---------------------------------------------------- 
		try_bool = df_country.groupby('Country/Region').max()['Delta C'] > 0 
		threshold_countries = try_bool.index[try_bool].tolist()
		 
		fig, ax = plt.subplots(1,1 ,figsize= full_w )


		for country in threshold_countries:
		    bool_country = df_country['Country/Region'] == country 
		    df_pl = df_country[bool_country] 
		    doubling_category = df_pl['doubling'].iloc[0]
		    pl1 = ax.plot( df_pl['Delta C' ],  df_pl['Confirmed'],
		            '.-' ,ms=3,lw=1.5, label=country,
		               color = cols[doubling_category])
		      
		    if country in notable_countries: 
		        y = df_pl['Confirmed'].iloc[-1]*0.98
		        x = df_pl['Delta C'].iloc[-1] + 0.5         
		        t = ax.text(x,y,country, ha="left", va="center" ,  bbox=bbox_props)
		         
		ax.set_yscale('log') 
		ax.grid(True,which="major", linestyle='-')  
		ax.grid(True,which="minor", linestyle=':', color=[.5,.5,.5],linewidth=0.6)  

		xCmax = df_country.loc[bool_nochina,'Delta C'].max() 
		yCmax = df_country['Confirmed'].max()
	 
		ax.yaxis.set_ticks( tick_list )
		ax.yaxis.set_ticklabels( tick_label_list)

		ax.set_xlim([0,xCmax+10])
		ax.set_ylim([100,yCmax*2])

		ax.set_xlabel("Days since passing "+ str(threshold_cases) + " confirmed cases") 
		ax.set_ylabel("Confirmed cases") 

		ax.annotate('Last update: '+str( df_country['Date'].iloc[-1]), 
		            [.3,round(yCmax,5)*1.1], color=[.5,.5,.5], style='italic')

		xy = []
		sc = plt.scatter(xy, xy, c=xy, vmin=0, vmax=1, cmap=cmap)
		cax = fig.add_axes([0.65, 0.19, 0.2, 0.02])
		cb = plt.colorbar(sc, cax = cax, orientation='horizontal') 

		cb.set_ticks(np.linspace(1/6,1,6)) 
		cb.set_ticklabels( ['20','15','10','7','5']) 
		cb.set_label('Doubling time in days (average over last 3)')
		cb.outline.set_visible(False)

		cb.ax.tick_params(which='major', length=15, width=1, direction='in',color='w')
	 
		fig_name= 'covid_country_caseslog' 
		if save_fig: 
		    plt.savefig('./figs/' + fig_name + '.png',
		            format='png', dpi=300,
		            transparent=  True,             
		            bbox_inches = 'tight', pad_inches = 0,
		            ) 

		# -------------------country deaths ---------------------------------------------------- 
		fig, ax = plt.subplots(1,1 ,figsize= full_w )
	 
		for country in threshold_countries:
		    bool_country = df_country['Country/Region'] == country 
		    df_pl = df_country[bool_country] 
		    doubling_category = df_pl['doublingD'].iloc[0]
		    pl1 = ax.plot( df_pl['Delta D' ],  df_pl['Death']  ,
		            '.-' ,ms=3,lw=1.5, label=country,
		               color = cols[doubling_category])
		      
		    if country in notable_countries:  
		        y = df_pl['Death'].iloc[-1]*0.98
		        x = df_pl['Delta D'].iloc[-1] + 0.5         
		        t = ax.text(x,y,country, ha="left", va="center" ,  bbox=bbox_props)
		         
		ax.set_yscale('log') 
		ax.grid(True,which="major", linestyle='-')  
		ax.grid(True,which="minor", linestyle=':', color=[.5,.5,.5],linewidth=0.6)   

		ax.yaxis.set_ticks( tick_list )
		ax.yaxis.set_ticklabels( tick_label_list)

		xDmax = df_country.loc[bool_nochina,'Delta D'].max()  
		yDmax = df_country['Death'].max()

		ax.set_xlim([0,xDmax+10])
		ax.set_ylim([25,yDmax*2]) 
		    
		ax.set_xlabel("Days since passing " + str(threshold_deaths)+ " deaths") 
		ax.set_ylabel("Deaths") 

		ax.annotate('Last update: '+str( df_country['Date'].iloc[-1]), 
		            [.3,round(yDmax,5)*1.1], color=[.5,.5,.5], style='italic')
		  
		xy = []
		sc = plt.scatter(xy, xy, c=xy, vmin=0, vmax=1, cmap=cmap)
		cax = fig.add_axes([0.65, 0.19, 0.2, 0.02])
		cb = plt.colorbar(sc, cax = cax, orientation='horizontal')  
		cb.set_ticks(np.linspace(1/6,1,6)) 
		cb.set_ticklabels( ['20','15','10','7','5']) 
		cb.set_label('Doubling time in days (average over last 3)')
		cb.outline.set_visible(False)

		cb.ax.tick_params(which='major', length=15, width=1, direction='in',color='w')

		fig_name= 'covid_country_deathslog' 
		if save_fig: 
		    plt.savefig('./figs/' + fig_name + '.png',
		            format='png', dpi=300,
		            transparent=  True,             
		            bbox_inches = 'tight', pad_inches = 0,
		            )  

		# ----------------plot grid of highlights-------------------------------------------------------
	 
		# sort countries by confirmed cases on last date
		bool_last = df_country['Date'] == df_country['Date'].max()
		sorted_countries = df_country[bool_last].sort_values(by=['Confirmed'], ascending=False )     
		sorted_names = sorted_countries['Country/Region'].tolist() 
		notable_countries = ['US','Japan','China','Italy' ,'Korea, South' ] 

		dy = 3
		dx = 6
		fig, ax = plt.subplots( dy,dx ,figsize=full_w )
		 
		for i, (ax_1, goal_country) in enumerate( zip(ax.reshape(-1), sorted_names[:(dy*dx)])):  
		    ax_1 = plot_highlight(ax_1, goal_country, df_country['Delta C'],
		                                            df_country['Confirmed'],
		                                            df_country['Country/Region'],
		                                            notable_countries)
		    ax_1 .grid(True )   
		    
		    if np.mod(i,dx) ==0:
		        for country in threshold_countries:
		            if (country in notable_countries) &( country not in goal_country):
		                bool_country = df_country['Country/Region'] == country 
		                df_pl = df_country[bool_country] 

		                y = df_pl['Confirmed'].iloc[-1]*1.1
		                x = df_pl['Delta C'].iloc[-1] + 1 
		                ax_1.annotate( country ,[x,y], color=emph_col, fontsize = 8, ha='center')
		    else: 
		        ax_1.axes.get_yaxis().set_ticklabels([])
		    if i< (dy-1)*dx:
		        ax_1.axes.get_xaxis().set_ticklabels([])
		         
		    xCmax = df_country['Delta C'].max() 
		    yCmax = df_country['Confirmed'].max()
		        
		    ax_1.set_xlim([0,xCmax+5])
		    ax_1.set_ylim([100,yCmax*3])
		      
		    
		ax[0,0].set_ylabel('Cases') 
		ax[0,0].annotate('Updated '+str( df_country['Date'].iloc[-1]), 
		            [6, 120], color=[.3,.3,.3], style='italic',fontsize=8)

		fig_name= 'covid_country_casesHighlightLog' 
		if save_fig: 
		    plt.savefig('./figs/' + fig_name + '.png',
		            format='png', dpi=300,
		            transparent=  True,             
		            bbox_inches = 'tight', pad_inches = 0,
		            )  

		# plot deaths highlight ------------------------------------------
		notable_countries = ['US','Japan','China','Italy' ,'Korea, South' ]
		dy = 3
		dx = 6
		fig, ax = plt.subplots( dy,dx ,figsize=full_w )
		 
		for i, (ax_1, goal_country) in enumerate( zip(ax.reshape(-1), sorted_names[:(dy*dx)])): 
		#     ax_1 = plot_highlight(ax_1, goal_country, df_country)  
		    
		    ax_1 = plot_highlight(ax_1, goal_country, df_country['Delta D'],
		                                            df_country['Death'],
		                                            df_country['Country/Region'],
		                                            notable_countries)
		    
		    ax_1 .grid(True )  
		    
		    if np.mod(i,dx) ==0:
		        for country in threshold_countries:
		            if (country in notable_countries) &( country not in goal_country):
		                bool_country = df_country['Country/Region'] == country 
		                df_pl = df_country[bool_country] 

		                y = df_pl['Death'].iloc[-1]*1.1
		                x = df_pl['Delta D'].iloc[-1] + 1 
		                ax_1.annotate( country ,[x,y], color=emph_col, fontsize = 8, ha='center')
		    else: 
		        ax_1.axes.get_yaxis().set_ticklabels([])
		    if i< (dy-1)*dx:
		        ax_1.axes.get_xaxis().set_ticklabels([])
		        
		        
		    xDmax = df_country['Delta D'].max() 
		    yDmax = df_country['Death'].max()
		    ax_1.set_xlim([0,xDmax+5])
		    ax_1.set_ylim([25,yDmax*3])
		      
		ax[0,0].set_ylabel('Deaths')

		ax[0,0].annotate('Updated '+str( df_country['Date'].iloc[-1]), 
		            [6, 28], color=[.3,.3,.3], style='italic',fontsize=8)

		fig_name= 'covid_country_deathsHighlightLog' 
		if save_fig: 
		    plt.savefig('./figs/' + fig_name + '.png',
		            format='png', dpi=300,
		            transparent=  True,             
		            bbox_inches = 'tight', pad_inches = 0,
		            )  




		#------------------map plot 
		fig, ax = plt.subplots(1,1 ,figsize=half_w)

		wp = world.plot(column='Cases', ax=ax, cmap='OrRd' );

		wp.set_xbound(-161,161)
		wp.set_ybound(-57,85) 

		vmin =   world['Cases'].min()  
		vmax =  world['Cases'].max() 
		sm = plt.cm.ScalarMappable(cmap='OrRd', norm=plt.Normalize(vmin=vmin, vmax=vmax))
	  
		sm._A = []
		cax = fig.add_axes([0.2, 0.2, 0.6, 0.03])
		cb = fig.colorbar(sm, cax=cax, orientation='horizontal')
	 

		tick_array =  [1,10,100,1000,10000, 50000 ] 
		log_cases = np.log( tick_array  )  
		cb.set_ticks( log_cases ) 
		cb.set_ticklabels( tick_array) 
		cb.set_label(' Daily case increaes  \n (average over last 7 days)')
		 
		ax.axis("off")

		ax.annotate('Updated '+str( df_country['Date'].iloc[-1]), 
		            [-161,-57], color=[.3,.3,.3], style='italic',fontsize=8)
		fig_name= 'covid_map' 
		if save_fig: 
		    plt.savefig('./figs/' + fig_name + '.png',
		            format='png', dpi=300,
		            transparent=  True,             
		            bbox_inches = 'tight', pad_inches = 0,
		            )  


		#-----daily cases worldwide-----------------------------------------------------
		df_pl = df_country.groupby( 'Date').sum() 
		df_pl['Date'] = df_pl.index  

		fig, ax = plt.subplots(1 ,2,figsize=(full_w[0],4))

		ax[0] = plot_daily( ax[0] , df_pl['Date'], df_pl['Daily Confirmed'] )
		ax[1] = plot_daily( ax[1] , df_pl['Date'], df_pl['Daily Death'] )

		ax[0].set_title('Worldwide Daily Confirmed')
		ax[1].set_title('Worldwide Daily Deaths')  
		ax[0].legend( )


		fig_name= 'covid_world_dailycases' 
		if save_fig: 
		    plt.savefig('./figs/' + fig_name + '.png',
		            format='png', dpi=300,
		            transparent=  True,             
		            bbox_inches = 'tight', pad_inches = 0,
		            )   
		#-----daily cases per country-----------------------------------------------------

		# sort countries by confirmed cases on last date
		bool_last = df_country['Date'] == df_country['Date'].max()
		sorted_countries = df_country[bool_last].sort_values(by=['Confirmed'], ascending=False )    
		sorted_countries.head(5)  
	 
		n_countries = 12
		top_countries = sorted_countries['Country/Region'][:n_countries].tolist()


		days = df_country['Date' ].unique() 

		dates = df_pl['Date' ].unique() 
		fig, ax = plt.subplots(n_countries ,2,figsize=( full_w[0],n_countries*3))
		 
		for i,country in enumerate( top_countries ):
		    df_pl = df_country[ df_country['Country/Region'] == country] 
		    
		    bool_measure = df_pl['Measure'].notnull() 
		    measures= df_pl.loc[bool_measure,['Measure','Date']] 
		     
		    plot_daily( ax[i,0] , df_pl['Date'], df_pl['Daily Confirmed'], measures)
		    plot_daily( ax[i,1] , df_pl['Date'], df_pl['Daily Death'],measures)
		 
		    # add comparison lines  
		    ax[i,0].plot( dates[[0,len(days)-1]], [1000,1000],'--',color='k', alpha = 0.5 )
		    ax[i,1].plot( dates[[0,len(days)-1]], [25,25],'--',color='k', alpha = 0.5 ) 
		    ax[i,0].set_ylabel( country )
		      
		ax[0,0].set_title('Daily Confirmed')
		ax[0,1].set_title('Daily Deaths') 

		# reverse the order 
		ax[0,0].legend(  ax[0,0].get_legend_handles_labels()[0][::-1] , 
		               ax[0,0].get_legend_handles_labels()[1] [::-1],
		               bbox_to_anchor=(0.42, .7))


		ax[0,0].annotate('1000 cases',[dates[0],1000*1.5])
		ax[0,1].annotate('25 deaths',[dates[0],25*1.5])


		ax[0,0].annotate('Updated '+str( df_country['Date'].iloc[-1]), 
		            [dt.date2num( dates[0] ) ,df_country['Daily Confirmed'].max()*(0.94-0.12)], 
		                 color=[.3,.3,.3], style='italic',fontsize=8)

		fig_name= 'covid_country_dailycases' 
		if save_fig: 
		    plt.savefig('./figs/' + fig_name + '.png',
		            format='png', dpi=300,
		            transparent=  True,             
		            bbox_inches = 'tight', pad_inches = 0,
		            )  





	# -----------state plots
 
	if plot_states: 
	# 	# plot states log -----------------------------

		try_bool = df_state.groupby('State').max()['Delta C'] > 0
		threshold_states = try_bool.index[try_bool].tolist()

		notable_states = ['New York','New Jersey','Michigan',"California",
					'Washington','Louisiana','Georgia','Utah' ]

		fig, ax = plt.subplots(1,1 ,figsize= full_w )  
		    
		xCmax = df_state['Delta C'].max()
		yCmax = df_state['Confirmed'].max()

		for state in threshold_states:
		    bool_state = df_state['State'] == state 
		    df_pl = df_state[bool_state] 

		    # print(state) 
		    # print(df_pl.tail() )

		    doubling_category = df_pl['doubling'].iloc[0]

		    pl1 = ax.plot( df_pl['Delta C' ],  df_pl['Confirmed'],
		            '.-' ,ms=3,lw=1.5, label=state,
		               color = cols[doubling_category])
		      
		    y = df_pl['Confirmed'].iloc[-1]*0.98
		    x = df_pl['Delta C'].iloc[-1] + 0.5      
		    
		    # print( x,y )

		    if (state in notable_states) & (0 <=  x <= xCmax+10) & (10<= y <= yCmax*2): 
		        t = ax.text(x,y,state, ha="left", va="center" ,  bbox=bbox_props)
		         
		ax.set_yscale('log') 
		ax.grid(True,which="major", linestyle='-')  
		ax.grid(True,which="minor", linestyle=':', color=[.5,.5,.5],linewidth=0.6)   
		 
		ax.yaxis.set_ticks( tick_list )
		ax.yaxis.set_ticklabels( tick_label_list)

		ax.set_xlim([0,xCmax+5])
		ax.set_ylim([100,yCmax*2])

		ax.set_xlabel("Days since passing "+ str(threshold_cases) + " confirmed cases") 
		ax.set_ylabel("Confirmed cases") 

		ax.annotate('Last update: '+str( df_state['Date'].iloc[-1]), 
		            [.3,round(yCmax,5)*1.1], color=[.5,.5,.5], style='italic')

		# cmap = ListedColormap(cols)
		xy = []
		sc = plt.scatter(xy, xy, c=xy, vmin=0, vmax=1, cmap=cmap)
		cax = fig.add_axes([0.65, 0.19, 0.2, 0.02])
		cb = plt.colorbar(sc, cax = cax, orientation='horizontal') 

		cb.set_ticks(np.linspace(1/6,1,6)) 
		cb.set_ticklabels( bin_labels) 
		cb.set_label('Doubling time in days (average over last 3)')
		cb.outline.set_visible(False)

		cb.ax.tick_params(which='major', length=15, width=1, direction='in',color='w')

		fig_name= 'covid_state_caseslog' 
		if save_fig: 
		    plt.savefig('./figs/' + fig_name + '.png',
		            format='png', dpi=300,
		            transparent=  True,             
		            bbox_inches = 'tight', pad_inches = 0,
		            )  


		# plot states deaths--------------------------------------------
		notable_states =   ['New York','New Jersey','Michigan',"California",'Washington','Louisiana',"Florida","Oregon"]

		fig, ax = plt.subplots(1,1 ,figsize= full_w )  
		     
		xDmax = df_state['Delta D'].max()
		yDmax = df_state['Deaths'].max()

		for state in threshold_states:
		    bool_state = df_state['State'] == state 
		    df_pl = df_state[bool_state] 
		    
		    doubling_category = df_pl['doublingD'].iloc[0]
		    pl1 = ax.plot( df_pl['Delta D' ],  df_pl['Deaths'],
		            '.-' ,ms=3,lw=1.5, label=state,
		               color = cols[doubling_category])
		       
		    y = df_pl['Deaths'].iloc[-1]*0.98
		    x = df_pl['Delta D'].iloc[-1] + 0.5         
		        
		    if (state in notable_states) & (0 <=  x <= xCmax+10) & (10<= y <= yCmax*2): 
		        t = ax.text(x,y,state, ha="left", va="center" ,  bbox=bbox_props)
		          
		ax.set_yscale('log') 
		ax.grid(True,which="major", linestyle='-')  
		ax.grid(True,which="minor", linestyle=':', color=[.5,.5,.5],linewidth=0.6)   

		ax.yaxis.set_ticks( tick_list )
		ax.yaxis.set_ticklabels( tick_label_list)

		ax.set_xlim([0,xDmax+5])
		ax.set_ylim([10,yDmax*2])

		ax.set_xlabel("Days since passing "+ str(threshold_deaths)+ " confirmed cases") 
		ax.set_ylabel("Confirmed deaths") 

		ax.annotate('Last update: '+str( df_state['Date'].iloc[-1]), 
		            [.3,round(yDmax,5)*1.1], color=[.5,.5,.5], style='italic')

		# cmap = ListedColormap(cols)
		xy = []
		sc = plt.scatter(xy, xy, c=xy, vmin=0, vmax=1, cmap=cmap)
		cax = fig.add_axes([0.65, 0.19, 0.2, 0.02])
		cb = plt.colorbar(sc, cax = cax, orientation='horizontal') 

		cb.set_ticks(np.linspace(1/6,1,6)) 
		cb.set_ticklabels(bin_labels) 
		cb.set_label('Doubling time in days (average over last 3)')
		cb.outline.set_visible(False)

		cb.ax.tick_params(which='major', length=15, width=1, direction='in',color='w')

		fig_name= 'covid_state_deathslog' 
		if save_fig: 
		    plt.savefig('./figs/' + fig_name + '.png',
		            format='png', dpi=300,
		            transparent=  True,             
		            bbox_inches = 'tight', pad_inches = 0,
		            )  
















	# ----------------plot grid of highlights-------------------------------------------------------
	 
		# sort states by confirmed cases on last date
		bool_last = df_state['Date'] == df_state['Date'].max()
		sorted_states = df_state[bool_last].sort_values(by=['Confirmed'], ascending=False )     
		sorted_names = sorted_states['State'].tolist()


		notable_states = ['New York', 'Washington'  ]


		dy = 3
		dx = 6

		fig, ax = plt.subplots( dy,dx ,figsize=full_w )
		 
		for i, (ax_1, goal_states) in enumerate( zip(ax.reshape(-1), sorted_names[:(dy*dx)])):  
		    ax_1 = plot_highlight(ax_1, goal_states, df_state['Delta C'],
		                                            df_state['Confirmed'],
		                                            df_state['State'],
		                                            notable_states)
		    ax_1 .grid(True )   
		    
		    if np.mod(i,dx) ==0:
		        for state in threshold_states:
		            if (state in notable_states) &( state not in goal_states):
		                bool_state = df_state['State'] == state
		                df_pl = df_state[bool_state] 

		                y = df_pl['Confirmed'].iloc[-1]*1.1
		                x = df_pl['Delta C'].iloc[-1] + 1 
		                ax_1.annotate( state ,[x,y], color=emph_col, fontsize = 8, ha='center')
		    else: 
		        ax_1.axes.get_yaxis().set_ticklabels([])
		    if i< (dy-1)*dx:
		        ax_1.axes.get_xaxis().set_ticklabels([])
		         
		    xCmax = df_state['Delta C'].max() 
		    yCmax = df_state['Confirmed'].max()
		        
		    ax_1.set_xlim([0,xCmax+5])
		    ax_1.set_ylim([100,yCmax*3])
		       
		ax[0,0].set_ylabel('Cases') 
		ax[0,0].annotate('Updated '+str( df_state['Date'].iloc[-1]), 
		            [6, 120], color=[.3,.3,.3], style='italic',fontsize=8)

		fig_name= 'covid_states_casesHighlightLog' 
		if save_fig: 
		    plt.savefig('./figs/' + fig_name + '.png',
		            format='png', dpi=300,
		            transparent=  True,             
		            bbox_inches = 'tight', pad_inches = 0,
		            )  
 
	# ----------------plot grid of deaths highlights-------------------------------------------------------
  
		# bool_last = df_state['Date'] == df_state['Date'].max()
		# sorted_states = df_state[bool_last].sort_values(by=['Confirmed'], ascending=False )     
		# sorted_names = sorted_states['State'].tolist() 

		notable_states = ['New York' ,'Washington', 'California' ]
 
		dy = 3
		dx = 6

		fig, ax = plt.subplots( dy,dx ,figsize=full_w )
		 
		for i, (ax_1, goal_states) in enumerate( zip(ax.reshape(-1), sorted_names[:(dy*dx)])):  
		    ax_1 = plot_highlight(ax_1, goal_states, df_state['Delta D'],
		                                            df_state['Deaths'],
		                                            df_state['State'],
		                                            notable_states)
		    ax_1 .grid(True )   
		    
		    if np.mod(i,dx) ==0:
		        for state in threshold_states:
		            if (state in notable_states) &( state not in goal_states):
		                bool_state = df_state['State'] == state
		                df_pl = df_state[bool_state] 

		                y = df_pl['Deaths'].iloc[-1]*1.1
		                x = df_pl['Delta D'].iloc[-1] + 1 
		                ax_1.annotate( state ,[x,y], color=emph_col, fontsize = 8, ha='center')
		    else: 
		        ax_1.axes.get_yaxis().set_ticklabels([])
		    if i< (dy-1)*dx:
		        ax_1.axes.get_xaxis().set_ticklabels([])
		         
		    xCmax = df_state['Delta D'].max() 
		    yCmax = df_state['Deaths'].max()
		        
		    ax_1.set_xlim([0,xCmax+5])
		    ax_1.set_ylim([10,yCmax*3])
		      
		    
		ax[0,0].set_ylabel('Deaths') 
		ax[0,0].annotate('Updated '+str( df_state['Date'].iloc[-1]), 
		            [6, 12 ], color=[.3,.3,.3], style='italic',fontsize=8)

		fig_name= 'covid_states_deathsHighlightLog' 
		if save_fig: 
		    plt.savefig('./figs/' + fig_name + '.png',
		            format='png', dpi=300,
		            transparent=  True,             
		            bbox_inches = 'tight', pad_inches = 0,
		            )  
 
		# # plot daily for US, by state data-----------------------------
		df_pl = df_state.groupby( 'Date').sum() 
		df_pl['Date'] = df_pl.index  

		fig, ax = plt.subplots(1 ,2,figsize=(full_w[0] ,4))

		ax[0] = plot_daily( ax[0] , df_pl['Date'], df_pl['Daily Confirmed'] )
		ax[1] = plot_daily( ax[1] , df_pl['Date'], df_pl['Daily Deaths'] )

		ax[0].set_title('US Daily Confirmed')
		ax[1].set_title('US Daily Deaths')  
		ax[0].legend( ax[0].get_legend_handles_labels()[0][::-1] , ax[0].get_legend_handles_labels()[1] [::-1])

		 

		 # plot daily per state
		bool_last = df_state['Date'] == df_state['Date'].max()
		sorted_states = df_state[bool_last].sort_values(by=['Confirmed'], ascending=False )    
		sorted_states.head(5)  

		n_state = 12
		top_state = sorted_states['State'][:n_state].tolist()

		dates = df_pl['Date' ].unique() 
		fig, ax = plt.subplots(n_state ,2,figsize=( full_w[0] ,n_state*3))

		n_correction = 1

		for i,country in enumerate( top_state ):
		    df_pl = df_state[ df_state['State'] == country]
		    
		    bool_measure = df_pl['Measure'].notnull() 
		    measures= df_pl.loc[bool_measure,['Measure','Date']] 
		     
		    plot_daily( ax[i,0] , df_pl['Date'], df_pl['Daily Confirmed'], measures)
		    plot_daily( ax[i,1] , df_pl['Date'], df_pl['Daily Deaths'],measures)
		 
		    # add comparison lines  
		    ax[i,0].plot( dates[[0,len(dates)-1]], [1000,1000],'--',color='k', alpha = 0.5 )
		    ax[i,1].plot( dates[[0,len(dates)-1]], [25,25],'--',color='k', alpha = 0.5 ) 
		    ax[i,0].set_ylabel( country )
		       
		ax[0,0].set_title('Daily Confirmed')
		ax[0,1].set_title('Daily Deaths') 

		ax[0,0].legend(  ax[0,0].get_legend_handles_labels()[0][::-1] , 
		               ax[0,0].get_legend_handles_labels()[1] [::-1],
		               bbox_to_anchor=(0.42, .7))

		ax[0,0].annotate('1000 cases',[dates[0],1000*1.5])
		ax[0,1].annotate('25 deaths',[dates[0],25*1.5])
 
		ax[0,0].annotate('Updated '+str(   dates[-1]  ), 
		            [dates[0], df_state['Daily Confirmed'].max()*(0.94-0.1)], 
		                color=[.3,.3,.3], style='italic',fontsize=8)

		fig_name= 'covid_states_dailycases'
		if save_fig: 
		    plt.savefig('./figs/' + fig_name + '.png',
		            format='png', dpi=300,
		            transparent=  True,             
		            bbox_inches = 'tight', pad_inches = 0,
		            )  

 
		# plot country map ------------------------------------------


		path = r'D:\Code_projects\Covid19_analysis\COVID-19\csse_covid_19_data\csse_covid_19_daily_reports'

		daily_reports = glob.glob(path + '\*.csv') 
		df = pd.DataFrame()
		for file in daily_reports :
		    df_temp = pd.read_csv( file, index_col=None, header=0) 
		    df = df.append(df_temp, sort=True) 

		# convert different datetimes to same datetime column 
		df['Last Update'] = pd.to_datetime(df['Last Update']   )
		df['Last_Update'] = pd.to_datetime(df['Last_Update']   )   #  
		cond = df['Last_Update'].isnull()
		df['Last Update'] = df['Last Update'].where(cond, df['Last_Update'] ) 
		df['Datetime']= pd.to_datetime(df['Last Update'] , unit='D'   ) 
		df['Date'] = df['Datetime'].dt.date

		cond = df['Country_Region'].isnull()
		df['Country/Region'] = df['Country/Region'].where(cond, df['Country_Region'] ) 

		cond = df['Province_State'].isnull()
		df['Province/State'] = df['Province/State'].where(cond, df['Province_State'] ) 
		 
		col_order = ['Date','Country/Region','Province/State','Active','Confirmed','Deaths','Recovered','Combined_Key' ]
		df = df[col_order]

		bool_US = df['Country/Region'] =='US' 
		# bool_last = df['Date'] > datetime.datetime(2020,3,22).date() 
		bool_last = df['Date'] > datetime.datetime(2020,3,23).date()
		 
		df_US = df[bool_US & bool_last ].copy() 
		 
		df_US =  df_US.groupby(['Province/State','Date']).sum().reset_index()  
		df_US = df_US.sort_values( by=['Province/State','Date']).reset_index(drop=True)  

	    
		US = gpd.read_file( 'geo_data\states.shp')
		AKratio = 0.4;  # scales Alaska 
		HIratio = 1.3 # scales Hawai 
		AKtrans = [25,-33] # moves Alaska south and east 
		HItrans = [34,4] # moves Hawaii east and north 
		 

		# get original polygons
		bool_alaska = US['STATE_NAME'] == 'Alaska'
		alaska_geom = US.loc[bool_alaska,'geometry'].iloc[0] 

		alaska_moved = shp.translate(alaska_geom, AKtrans[0], AKtrans[1])  
		centroid = alaska_moved.centroid
		alaska_scaled = shp.scale( alaska_moved, xfact=AKratio, yfact=AKratio, origin=centroid)
		US['geometry'][50] =  alaska_scaled

		bool_hawaii = US['STATE_NAME'] == 'Hawaii'
		hawaii_geom = US.loc[bool_hawaii,'geometry'].iloc[0] 

		hawaii_moved = shp.translate(hawaii_geom, HItrans[0], HItrans[1])  
		centroid = hawaii_moved.centroid
		hawaii_scaled = shp.scale( hawaii_moved, xfact=HIratio, yfact=HIratio, origin=centroid)
		US['geometry'][0] =  hawaii_scaled
	 
		states = df_US['Province/State'].unique().tolist()
		dates = df_US['Date'].unique() 

		for state in states: 
		#     print(state)
		    bool_state = df_US['Province/State'] == state 
		    bool_date = df_US['Date'] == dates[-1]
		    bool_prior = df_US['Date'] == dates[-7] 
		    if (bool_state & bool_date).sum() > 0:
		        now_cases = df_US[bool_state & bool_date ]['Confirmed'].iloc[0]
		        prior_cases = df_US[bool_state & bool_prior ]['Confirmed'].iloc[0]
		        latest_cases = (now_cases-prior_cases)/7
		    else:
		        latest_cases = 0 
		         
		    df_US.loc[bool_state ,'Cases'] = np.log(latest_cases + 2)
		    
		df_US = df_US.rename(columns={'Province/State':'STATE_NAME'}) 

		df_US = df_US[bool_date] 
		US= pd.merge(US, df_US, how='left', on=['STATE_NAME'])
		df_US.head()  

		fig, ax = plt.subplots(1,1 ,figsize=half_w )

		wp = US.plot(column='Cases', ax=ax, cmap='OrRd'   );

		wp.set_xbound(-135,-66)
		wp.set_ybound(20,49.5)  

		vmin =    US['Cases'].min()
		vmax =  ( US['Cases'].max() )
		 
		sm = plt.cm.ScalarMappable(cmap='OrRd', norm=plt.Normalize(vmin=vmin, vmax=vmax)) 
		 
		# fake up the array of the scalar mappable. Urgh...
		sm._A = []
		cax = fig.add_axes([0.2, 0.25, 0.6, 0.03])
		cb = fig.colorbar(sm, cax=cax, orientation='horizontal')
		  
		tick_array =  [20,40,100,400,1000,4000,10000 ] 
		log_cases = np.log( tick_array  )  
		cb.set_ticks( log_cases ) 
		cb.set_ticklabels( tick_array) 
		cb.set_label(' Daily case increaes  \n (average over last 7 days)')

		ax.axis("off")


		ax.annotate('Updated '+str( df_US['Date'].iloc[-1]), 
		            [-135,22 ], color=[.3,.3,.3], style='italic',fontsize=8)
		fig_name= 'covid_state_map' 

		if save_fig: 
		    plt.savefig('./figs/' + fig_name + '.png',
		            format='png', dpi=300,
		            transparent=  True,             
		            bbox_inches = 'tight', pad_inches = 0,
		            )   
 

	# show all figures ----------------------------------
	if show_plot:
		plt.show() 