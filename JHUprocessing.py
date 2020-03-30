import pandas as pd

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
