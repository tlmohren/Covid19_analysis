import pandas as pd
import matplotlib.pyplot as plt 
import matplotlib.dates as mdates   
from matplotlib.dates import date2num       #-->Update   
import numpy as np
import os

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
	countries_to_highlight, threshold_cases): 

    dot_col = np.ones((3))*0.8 
    emph_col = [0.5,0.5,0.5]  
    goal_col = "r"
    dot_alpha = 1 

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
    
    weeks = mdates.DayLocator(bymonthday=[1], interval=1, tz=None)
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



def save_fig( figs_dir, fig_name ): 
    
    fig_fullname = os.path.join( figs_dir, fig_name ) 
    print('Saving to: ' + fig_fullname + '.png') 
    plt.savefig( fig_fullname+ '.png',
            format='png', dpi=300,
            transparent=  True,             
            bbox_inches = 'tight', pad_inches = 0, 
               ) 
