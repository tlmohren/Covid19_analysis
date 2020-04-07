import pandas as pd
import matplotlib.pyplot as plt 

import matplotlib.dates as mdates  
import numpy as np
from datetime import timedelta
from matplotlib.dates import date2num       #-->Update 

import JHUprocessing as jp
from matplotlib.colors import ListedColormap
 

####--------------------parameters --------------------------------------

# families = ['serif', 'sans-serif', 'cursive', 'fantasy', 'monospace']
# plt.rcParams["font.family"] = families[1]

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
# [230,245,152],
[171,221,164],
# [102,194,165],
[50,136,189]]) /255 
cols = np.flipud(cols)
cmap = ListedColormap(cols)


threshold_cases = 100
threshold_deaths = 25


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










# ####------------------functions-- --------------------------------------
if __name__ == '__main__':
	print('run script directly') 

	path = r'D:\Code_projects\Covid19_analysis\COVID-19\csse_covid_19_data\csse_covid_19_time_series'
	file_list = ['\\time_series_covid19_confirmed_global.csv',
	         '\\time_series_covid19_deaths_global.csv',
	         '\\time_series_covid19_recovered_global.csv'] 

	df_country = jp.merge_countrydf(path, file_list) 

	# drop countries: like diamond princess 
	bool_other = df_country['Country/Region'].str.contains( 'Princess' , regex=False)
	df_country.drop( df_country[bool_other].index, inplace=True) 

 
	last_day = df_country['Date'].max()
	bool_last = df_country['Date'] == last_day
	df_country.loc[bool_last,'Confirmed']  > threshold_cases 
	countries = df_country['Country/Region'].unique() 
	threshold_countries = []

	for country in countries: 
	    bool_country = df_country['Country/Region'] == country  
	    df_temp = df_country[bool_country].copy()
	    
	    bool_threshold_cases = df_temp['Confirmed'] >= threshold_cases
	    if bool_threshold_cases.sum() > 0: 
	        day0 = df_temp.loc[bool_threshold_cases,'Date'].iloc[0]
	        threshold_countries.append(country) 
	    else: 
	        day0 = last_day + timedelta(days=1) 

	    newdays = (df_temp['Date'] - day0).dt.days  
	    
	    df_country.loc[bool_country,'Delta C'] = newdays
	     
	    
	    bool_threshold_death = df_temp['Death'] >= threshold_deaths
	    if bool_threshold_death.sum() > 0:
	        day0 = df_temp['Date'][bool_threshold_death].iloc[0]
	    else:
	        day0 = last_day + timedelta(days=1) 
	        
	    newdays = (df_temp['Date'] - day0).dt.days 
	    df_country.loc[bool_country,'Delta D'] = newdays 
    
    
    # correct for china plotting


	china_add = 6
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

	# adding doubling rate column
	# find doubling rate, average over last 3 days?  
	#-----------------------------------------------------------------------
	average_period = 3

	last_day = df_country['Date'].max() #- timedelta(days=3)
	prior_day = df_country['Date'].max() - timedelta(days=average_period)

	bool_last = df_country['Date'] == last_day
	bool_prior = df_country['Date'] == prior_day
	  
	for country in countries: 
	    bool_country = df_country['Country/Region'] == country   
	    
	    ratio = df_country.loc[bool_last & bool_country,'Confirmed'].values[0]  / \
	            df_country.loc[bool_prior & bool_country,'Confirmed'].values[0]   
	    
	    daily_ratio = ratio**(1/average_period)  
	    
	    df_country.loc[bool_country,'ratio'] = daily_ratio

	    bin_array = np.array( [0, 2.**(1./20), 2.**(1./15), 2.**(1./10), 2.**(1./7), 2.**(1./5)  ,np.inf ]) 
	df_country['doubling'] = pd.cut( df_country['ratio'],   bin_array ,labels=range(len(bin_array)-1) , include_lowest=True )
	df_country['doubling'].unique()


	# find doubling rate, average over last 3 days?  
	average_period = 3

	last_day = df_country['Date'].max() #- timedelta(days=3)
	prior_day = df_country['Date'].max() - timedelta(days=average_period)

	bool_last = df_country['Date'] == last_day
	bool_prior = df_country['Date'] == prior_day
	  
	for country in countries: 
	    bool_country = df_country['Country/Region'] == country   
	    
	    ratio = df_country.loc[bool_last & bool_country,'Death'].values[0]  / \
	            df_country.loc[bool_prior & bool_country,'Death'].values[0]   
	    
	    daily_ratio = ratio**(1/average_period)   
	    if np.isnan(ratio):
	        ratio = 1
	        
	    if np.isinf(ratio):
	        ratio = 100

	    df_country.loc[bool_country,'ratioD'] = daily_ratio

	    bin_array = np.array( [-1, 2.**(1./20), 2.**(1./15), 2.**(1./10), 2.**(1./7), 2.**(1./5)  ,np.inf ]) 

	df_country['doublingD'] = pd.cut( df_country['ratioD'],   bin_array ,labels=range(len(bin_array)-1) , include_lowest=True )
	df_country['doublingD'] = df_country['doublingD'].fillna(0)
	df_country['doublingD'].unique()
	# df_country['ratioD'] 



	# load csv file of measures per country 
	df_m = pd.read_csv( "measures_per_country.csv", index_col=None ) 
	df_m['Date'] = pd.to_datetime( df_m['Date'] ).dt.date 

	# add measures to additional column
	for i,row in df_m.iterrows(): 
	    country = row['Country/Region']
	    date = row['Date']
	    bool_loc = (df_country['Country/Region'] == country) & (df_country['Date'] == date) 
	    df_country.loc[bool_loc,'Measure'] = row['Measure']






	df_country['Daily Confirmed'] = np.nan
	df_country['Daily Death'] = np.nan

	days = df_country['Date'].unique()  

	bool_day0 = df_country['Date'] == days[0]
	df_country.loc[bool_day0,'Daily Confirmed'] = 0
	df_country.loc[bool_day0,'Daily Death'] = 0
	 
	for day in days[1:]:     
	    
	    bool_day = df_country['Date'] == day 
	    bool_prior = df_country['Date'] == ( day- timedelta(days=1))  

	    delta = df_country[bool_day]['Confirmed'].values - df_country[bool_prior]['Confirmed'].values
	    df_country.loc[bool_day,'Daily Confirmed'] = delta 
	    
	    
	    delta = df_country[bool_day]['Death'].values - df_country[bool_prior]['Death'].values
	    df_country.loc[bool_day,'Daily Death'] = delta 
	 




	    # ---- world map 
	# world['Cases'] = 0 
	# countries = world['name'].tolist()
	 
	# dates = df_country['Date'].unique() 

	# for country in countries: 
	#     bool_country = df_country['Country/Region'] == country 
	#     bool_date = df_country['Date'] == dates[-1]
	#     bool_prior = df_country['Date'] == dates[-7] 
	#     if (bool_country & bool_date).sum() > 0:
	#         now_cases = df_country[bool_country & bool_date ]['Confirmed'].iloc[0]
	#         prior_cases = df_country[bool_country & bool_prior ]['Confirmed'].iloc[0]
	#         latest_cases = (now_cases-prior_cases)/7
	#     else:
	#         latest_cases = 0 
	    
	#     bool_world = world['name'] == country 
	# #     world.loc[bool_world,'Cases'] = latest_cases  
	#     world.loc[bool_world,'Cases'] = np.log(latest_cases+1) 





	print( df_country.columns ) 



	#-----------------------------------------------------------------------


	bbox_props = dict(boxstyle="round,pad=0.1", fc="w", ec="w", lw=2, alpha = 0.5)

	notable_countries = ['US','Italy','Spain','China', 'France','Germany','Iran',
	                     'United Kingdom','Switzerland','Turkey','Netherlands','Austria',
	                        'Korea, South','Brazil' ,'Singapore','Sweden','Japan',
	                        'Dominican Republic', 'Russia','Ukraine','Vietnam']

	fig, ax = plt.subplots(1,1 ,figsize= full_w )
	cmap = plt.cm.jet  # define the colormap
	for country in threshold_countries:
	    bool_country = df_country['Country/Region'] == country 
	    df_pl = df_country[bool_country] 
	    doubling_category = df_pl['doubling'].iloc[0]
	    pl1 = ax.plot( df_pl['Delta C' ],  df_pl['Confirmed'],
	            '.-' ,ms=3,lw=1.5, label=country,
	               color = cols[doubling_category])
	      
	    if country in notable_countries:
	#     if country in countries:
	        y = df_pl['Confirmed'].iloc[-1]*0.98
	        x = df_pl['Delta C'].iloc[-1] + 0.5         
	        t = ax.text(x,y,country, ha="left", va="center" ,  bbox=bbox_props)
	         
	ax.set_yscale('log') 
	ax.grid(True,which="major", linestyle='-')  
	ax.grid(True,which="minor", linestyle=':', color=[.5,.5,.5],linewidth=0.6)  
	# ax.set_title('Number of Cases in top countries (last update: ' + str( df_country['Date'].iloc[-1]) + ')' ) 
	# ax.set_xlim([0,70])

	ymax = df_country['Confirmed'].max()


	ax.yaxis.set_ticks([1e2,2e2,5e2,1e3,2e3,5e3,1e4,2e4,5e4,1e5,2e5,5e5,1e6,2e6,5e6,])
	ax.yaxis.set_ticklabels([100,200,500, 1000,2000,5000, '10k','20k','50k', '100k','200k','500k','1m','2m','5m'])

	ax.set_xlim([0,xCmax+10])
	ax.set_ylim([100,ymax*2])

	ax.set_xlabel("Days since passing "+ str(threshold_cases) + " confirmed cases") 
	ax.set_ylabel("Confirmed cases") 

	ax.annotate('Last update: '+str( df_country['Date'].iloc[-1]), 
	            [.3,round(ymax,5)*1.1], color=[.5,.5,.5], style='italic')


	xy = []
	sc = plt.scatter(xy, xy, c=xy, vmin=0, vmax=1, cmap=cmap)
	cax = fig.add_axes([0.65, 0.19, 0.2, 0.02])
	cb = plt.colorbar(sc, cax = cax, orientation='horizontal') 

	cb.set_ticks(np.linspace(1/6,1,6)) 
	cb.set_ticklabels( ['20','15','10','7','5']) 
	cb.set_label('Doubling time in days (average over last 3)')
	cb.outline.set_visible(False)

	cb.ax.tick_params(which='major', length=15, width=1, direction='in',color='w')
 

	# # # # # # save fig  -----------------------------------------------------------------------
	fig_name= 'covid_country_caseslog'
	save_fig = True
	if save_fig: 
	    plt.savefig('./figs/' + fig_name + '.png',
	            format='png', dpi=300,
	            transparent=  True,             
	            bbox_inches = 'tight', pad_inches = 0,
	            ) 


 	# -----------------------------------------------------------------------
	# -------------------country deaths ----------------------------------------------------
	# -----------------------------------------------------------------------
	bbox_props = dict(boxstyle="round,pad=0.1", fc="w", ec="w", lw=2, alpha = 0.5)

	notable_countries = ['US','Italy','Spain','China', 'France','Germany','Iran',
	                     'United Kingdom','Switzerland','Turkey','Netherlands','Austria',
	                        'Korea, South' ,'Japan',
	                        'Dominican Republic', 'Russia','Ukraine' ]

	fig, ax = plt.subplots(1,1 ,figsize= full_w )


	cmap = plt.cm.jet  # define the colormap
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

	ax.yaxis.set_ticks([1e2,2e2,5e2,1e3,2e3,5e3,1e4,2e4,5e4,1e5,2e5,5e5,1e6,2e6,5e6,])
	ax.yaxis.set_ticklabels([100,200,500, 1000,2000,5000, '10k','20k','50k', '100k','200k','500k','1m','2m','5m'])


	yDmax = df_country['Death'].max()
	ax.set_xlim([0,xDmax+10])
	ax.set_ylim([25,yDmax*2])
	 
	    
	# ax.set_xlabel("Days since passing 100 Death cases") 
	ax.set_xlabel("Days since passing " + str(threshold_deaths)+ " deaths") 
	ax.set_ylabel("Deaths") 

	ax.annotate('Last update: '+str( df_country['Date'].iloc[-1]), 
	            [.3,round(yDmax,5)*1.1], color=[.5,.5,.5], style='italic')
	 
	  
	cmap = ListedColormap(cols)
	xy = []
	sc = plt.scatter(xy, xy, c=xy, vmin=0, vmax=1, cmap=cmap)
	cax = fig.add_axes([0.65, 0.19, 0.2, 0.02])
	cb = plt.colorbar(sc, cax = cax, orientation='horizontal')  
	cb.set_ticks(np.linspace(1/6,1,6)) 
	cb.set_ticklabels( ['20','15','10','7','5']) 
	cb.set_label('Doubling time in days (average over last 3)')
	cb.outline.set_visible(False)

	cb.ax.tick_params(which='major', length=15, width=1, direction='in',color='w')

	plt.show()
	# # # # # save fig  -----------------------------------------------------------------------
	fig_name= 'covid_country_deathslog'
	save_fig = True
	if save_fig: 
	    plt.savefig('./figs/' + fig_name + '.png',
	            format='png', dpi=300,
	            transparent=  True,             
	            bbox_inches = 'tight', pad_inches = 0,
	            )  

	# -----------------------------------------------------------------------
	# -----------------------------------------------------------------------
	# -----------------------------------------------------------------------
 