import datetime
import numpy as numpy
import os
import pandas as pd
import smartsheet as ss

starttime = datetime.datetime.now()

version = ss.__version__
print(f"Smartsheet SDK version is: {version} \n")

token = os.getenv('SMARTSHEET_ACCESS_TOKEN')
print(f"Smartsheet access token was {token} \n")

#compass_tracker_filename = 'ConsolidatedReport_20200904_110510.xlsx'

#Initialize the smartsheet_client.Uses the API token in the environment variable "SMARTSHEET_ACCESS_TOKEN"
smartsheet_client = ss.Smartsheet(token)

smartsheet_client.errors_as_exceptions(True)

response = smartsheet_client.Sheets.list_sheets(include_all=True)

print(f"Response status code is {response.request_response.status_code} \n")

sheets = response.data

sheet_name = "Compass Request Tracker - Targeting Campaign"

# Pull the Smartsheet sheet we're looking for from the collection of all the sheets in the response-data

def get_sheet_id_from_sheets(sheet_name):
    for _, sheet in enumerate(sheets, 1):
        if sheet.name == sheet_name:
            sheet_id = sheet.id
            return sheet_id
        
        if not sheet.id:
            errmsg = f"Cannot find the sheet from this sheet_name: {sheet_name} \n"
            print(errmsg)
            raise Exception(errmsg)


sheet_id = get_sheet_id_from_sheets(sheet_name)

print(f"We found {sheet_name} with ID of {sheet_id}. \n Starting the data transformation & update work! Please hold on......\n")

# get the actual sheet object we want and make it the variable named "sheet"
sheet = smartsheet_client.Sheets.get_sheet(sheet_id)


#Create a mapping of column names => column id's
column_map = {}
for column in sheet.columns:
    column_map[column.title] = column.id

#Create the inverted mapping of column id's => column names
inverted_column_map = {value: key for key, value in column_map.items()}

columns_to_update = ['Customer Name']

result = sheet.to_dict()
columns = list(inverted_column_map.values())

print(columns)


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


forecast_stage_column =  column_map['Forecast Stage']

# Now bring in the Compass tracker excel export which has determined the rows with duplicate deal-id's
# we have to identify them so that we do not double-count bookings or pipeline values from SFDC

print("Reading in the Compass Tracker Data from the Excel export! \n")

compass_tracker_path = r'C:\Users\phsheari\Documents\SFDC Data\PIPELINE UPDATE\SFDC_Trackerfile.pkl'

trkr = pd.read_pickle(compass_tracker_path)

print("Applying the Compass Tracker Data filter criteria! \n")

#dataframe filter criteria:
condition1 = (trkr['Dupechk']==1)
condition2 = ~(trkr['Deal ID'] == -44444)
condition3 = ~(trkr['Forecast Stage']=='5 - Closed Won')

#check value (Count) prior to executing this change in the dataframe
count_prior = trkr['Forecast Stage'].value_counts()[0]
print(f"The Duplicated Deal ID row count prior to the update is {count_prior}.\n")

print("Applying the Compass Tracker Data: "" 7 - Duplicate Request "" update! \n")

#Duplicate Deal ID assignment
trkr.loc[(condition1 & condition2 & condition3),'Forecast Stage'] = '7 - Duplicate Request'

count_post = trkr['Forecast Stage'].value_counts()[0]
print(f"The Duplicated Deal ID row count after the update is {count_post}.\n")


print(f"Building new dataset of updated rows to update back into Smartsheet: {sheet_name}. \n\n")
#Find the request IDs to update in the Smartsheet dataset
requestids_to_update = trkr.loc[(condition1 & condition2 & condition3),'Request ID']
update_list =  requestids_to_update.astype(str).to_list()

### Build a Smartsheet section - -------------------------------------
# Note: Smartsheet is expecting an array of row objects that are in the following example format:
# ///
# {"cells": [{"columnId": 8342641216644996, "value": "7 - Duplicate Request"}], "id": 1692013020899204}
# {"cells": [{"columnId": 8342641216644996, "value": "7 - Duplicate Request"}], "id": 7040037578401668}
# {"cells": [{"columnId": 8342641216644996, "value": "7 - Duplicate Request"}], "id": 1410538044188548}
# {"cells": [{"columnId": 8342641216644996, "value": "7 - Duplicate Request"}], "id": 4999343997249412}
# {"cells": [{"columnId": 8342641216644996, "value": "7 - Duplicate Request"}], "id": 1867934881343364}
# {"cells": [{"columnId": 8342641216644996, "value": "7 - Duplicate Request"}], "id": 5738215811114884}
# ///

# Helper function to find cell in a row
def get_cell_by_column_name(row, column_name):
    column_id = column_map[column_name]
    return row.get_column(column_id)

# Return a new Row with updated cell values, else None to leave unchanged
def evaluate_row_and_build_updates(source_row):
    request_cell = get_cell_by_column_name(source_row, "Request ID")
    request_value = request_cell.display_value
    if request_value in update_list:
        
    # Build new cell value
        new_cell = smartsheet_client.models.Cell()  # instantiate a new cell entity
        new_cell.column_id = column_map["Forecast Stage"]   # set the properties of the new cell, in this case, the column ID returned from the dict
        new_cell.value = '7 - Duplicate Request'       # set the value of the new cell

    # Build the row to update
        new_row = smartsheet_client.models.Row()
        new_row.id = source_row.id
        new_row.cells.append(new_cell)

        return new_row
    
    return None

# Accumulate rows being updated here
rows_to_update = []

for row in sheet.rows:
    rowToUpdate = evaluate_row_and_build_updates(row)
    if rowToUpdate is not None:
        rows_to_update.append(rowToUpdate)


update_count = len(rows_to_update)
print(f"We found {update_count} rows to update in sheet: {sheet_name}. \n")

if rows_to_update:
    print(f"Writing {update_count} rows back to sheet id: {sheet.id}. \n\n" )
    result = smartsheet_client.Sheets.update_rows(sheet_id, rows_to_update)
else:
    print("No update available")


endtime = datetime.datetime.now()

elapsed_time = endtime - starttime

print(f"It required {elapsed_time} seconds for this update to complete.") 

