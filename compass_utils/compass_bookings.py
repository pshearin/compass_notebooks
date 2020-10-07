import datetime
import numpy as numpy
import os
import pandas as pd
import smartsheet as ss



version = ss.__version__
print(f"Smartsheet SDK version is: {version} \n")

token = os.getenv('SMARTSHEET_ACCESS_TOKEN')
print(f"Smartsheet access token was {token} \n")

#Initialize the smartsheet_client.Uses the API token in the environment variable "SMARTSHEET_ACCESS_TOKEN"
smartsheet_client = ss.Smartsheet(token)

smartsheet_client.errors_as_exceptions(True)

response = smartsheet_client.Sheets.list_sheets(include_all=True)

print(f"Response status code is {response.request_response.status_code} \n")

sheets = response.data

sheet_name = "Compass Bookings"

# Pull the Smartsheet sheet we're looking for from the collection of all the sheets in the response-data

def get_sheet_id_from_sheets(sheet_name):
    for _, sheet in enumerate(sheets, 1):
        if sheet.name == sheet_name:
            sheet_id = sheet.id
            return sheet_id
        
    if not sheet_id:
        errmsg = f"Cannot find the sheet from this sheet_name: {sheet_name} \n"
        print(errmsg)
        raise Exception(errmsg)


sheet_id = get_sheet_id_from_sheets(sheet_name)
# get the actual sheet object we want and make it the variable named "sheet"
sheet = smartsheet_client.Sheets.get_sheet(sheet_id)
#Create a mapping of column names => column id's
column_map = {}
for column in sheet.columns:
    column_map[column.title] = column.id

#Create the inverted mapping of column id's => column names
inverted_column_map = {value: key for key, value in column_map.items()}

result = sheet.to_dict()
columns = list(inverted_column_map.values())

# build the dataset, row by row ---------------------------------------------------
result_list = []
for row in result['rows']:
    temp_df = pd.DataFrame(row['cells'], index=columns)
    try: 
        if 'value' in temp_df.columns:
            result_list.append(temp_df['value'])
#        else: 
#            continue
    except:
        print(temp_df.columns)
        print(temp_df)
        import pdb; pdb.set_trace()


data_df = pd.concat(result_list, axis=1)       # concatenate the result_list of rows into a single dataframe. where the index are all the column names
data_dft = data_df.T                           # tranpose the dataframe created above so that the index becomes the columns and the columns became the index
data_dft.reset_index(drop=True, inplace=True)  # reset the index to a 0-based enumeration