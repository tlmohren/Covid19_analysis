import pandas as pd
import matplotlib.pyplot as plt 

def merge_data(path, file_list):
    
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
    
####--------------------fonts---------------------------------------

families = ['serif', 'sans-serif', 'cursive', 'fantasy', 'monospace']

plt.rcParams["font.family"] = families[1]
# plt.rcParams['text.usetex'] = True
# plt.rcParams['text.latex.preamble'] = [r'\usepackage{amsmath}'] #for \text command


# plt.style.use('latex_scientificPaperStyle.mplstyle')

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