import numpy as np
import pandas as pd 
import datetime as dt

excel_file_path_sfdc_version = r'C:\Users\phsheari\Documents\SFDC Data\PIPELINE UPDATE\SFDC_Trackerfile.pkl'

df = pd.read_pickle(excel_file_path_sfdc_version)

step_one = df[['Request ID','Readout_Date']] 
step_one['Readout_Date'] = step_one['Readout_Date'].apply(lambda x: pd.to_datetime(x))

#A function to stringify the various possible elements in the dataframe with a float data-type
def stringify_element(m):
    a = pd.NA
    if pd.isnull(m):  # if did is null or nan
        return pd.NA
    elif type(m) == np.float64:
        return str(int(m))
    elif type(m) == float:
        return str(int(m))
    elif type(m) == np.int64:
        return str(m)
    elif type(m) == int:
        return str(m)
    elif type(m) == str:
        try:
            a = m.replace('"','').replace('&',',').replace('(','').replace(')','').replace(':',',').replace(' ',',').replace('\n',',').replace(',,',',').strip().split(',') 
            return a
        except:
            import pdb; pdb.set_trace()
    else:
        return m

guidf = df[['Request ID','GUID']]
guidf['GUID'] = guidf['GUID'].apply(stringify_element)
guidf.set_index('Request ID', inplace=True)
guidf = guidf.explode('GUID')
guidf.reset_index(inplace=True)
guidf.dropna(inplace=True)

""" guidlist = []
for i,guid in guidf['GUID'].items():
    if isinstance(guid,list):
        for e in guid:
            if (pd.notnull(e) or e != ''):
                if e.isdigit():
                    guidlist.append((i,e))
    else:
        guidlist.append((i,guid)) """

guidf['BADGUID'] = guidf['GUID'].str.isalpha()
guidf['BADLENGTH'] = guidf['GUID'].apply(lambda x: len(x)> 10)
guidf.drop(guidf.loc[guidf['BADGUID']==True].index, inplace=True)
guidf.drop(guidf.loc[guidf['BADLENGTH']==True].index, inplace=True)
guidf.drop(guidf.loc[~(guidf['GUID'].str.isdigit())].index, inplace=True)
guidf.drop(columns = ['BADGUID','BADLENGTH'], inplace=True)
guidf['GUID'] = guidf['GUID'].astype(int)

readouts = pd.merge(guidf, step_one, on='Request ID').dropna()

def get_readout_dates(input_guid: int):
    return readouts.loc[(readouts['GUID']==input_guid) & (readouts['Readout_Date'].notnull()),'Readout_Date'].values[0]


def get_readout_dataframe():
    return readouts