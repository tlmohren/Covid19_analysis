import pandas as pd
import matplotlib.pyplot as plt 

import matplotlib.dates as mdates  
import numpy as np
from datetime import timedelta
from matplotlib.dates import date2num       #-->Update 
 
from matplotlib.colors import ListedColormap
 

####--------------------parameters --------------------------------------
 

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


 
	# ---------------------------------------------------------
	# --------------plotting log stuff ------------------------
	# ---------------------------------------------------------
 
	# -------------------country cases ---------------------------------------------------- 

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
	save_fig = True
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
	save_fig = True
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
	save_fig = True
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
	save_fig = True
	if save_fig: 
	    plt.savefig('./figs/' + fig_name + '.png',
	            format='png', dpi=300,
	            transparent=  True,             
	            bbox_inches = 'tight', pad_inches = 0,
	            )  

	# show all figures ----------------------------------
	plt.show()