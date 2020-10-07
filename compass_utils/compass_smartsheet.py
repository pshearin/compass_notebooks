
import datetime as dt 
import numpy as np 
import os
import pandas as pd 
from smartsheet import Smartsheet

REFERENCEFILE = r'C:\Users\phsheari\Documents\Compass Tracker Backups\ConsolidatedReport.xlsx'

class CompassSmartsheet:

    def __init__(self, filename = REFERENCEFILE, page = 1, pagesize=10000):
        self.token = os.getenv("SMARTSHEET_ACCESS_TOKEN")
        self.pagenum = page
        self.pagesize = pagesize
        self.today_timestamp = dt.datetime.now().isoformat()[:19]
        self.hour = int(self.today_timestamp[11:13])
        self.meridian = self.get_meridian(self.hour)
        self.last_updated = str(self.today_timestamp[:10]) + ' ' + str(self.today_timestamp[11:16]) + ' ' + self.meridian + ' ET'
        self.reference_file = filename

        self.region_dict = {'AMERICAS_MISC':'AMERICAS_MISC',
               'AMERICAS_SP':'AMERICAS_SP',
               'ANZ AREA':'ANZ_AREA',
               'ANZ_AREA':'ANZ_AREA',
               'APJ_SP':'APJ_SP',
               'ASEAN_AREA':'ASEAN_AREA',
               'CANADA':'CANADA',
               'EMEAR_GERMANY':'EMEAR_GERMANY',
               'EMEAR-GERMANY':'EMEAR_GERMANY',
               'EMEAR_MEA':'EMEAR_MEA',
               'EMEAR-MEA':'EMEAR_MEA',
               'EMEAR_SP':'EMEAR_SP',
               'EMEAR-SP':'EMEAR_SP',
               'EMEAR-CENTRAL':'EMEAR_CENTRAL',
               'EMEAR_CENTRAL':'EMEAR_CENTRAL',
               'EMEAR-NORTH':'EMEAR_NORTH',
               'EMEAR_NORTH':'EMEAR_NORTH',
               'EMEAR-SOUTH':'EMEAR_SOUTH',
               'EMEAR_SOUTH':'EMEAR_SOUTH',
               'EMEAR-REGION':'EMEAR_REGION',
               'EMEAR_REGION':'EMEAR_REGION',
               'EMEAR-UKI':'EMEAR_UKI',
               'EMEAR_UKI':'EMEAR_UKI',
               'EMEAR_UNALLOCATED':'EMEAR_UNALLOCATED',
               'GLOBAL ENTERPRISE SEGMENT':'GES',
               'GES':'GES',
               'GREATER_CHINA':'GREATER_CHINA',
               'GREATER-CHINA':'GREATER_CHINA',
               'INDIA-AREA':'INDIA_AREA',
               'INDIA_AREA':'INDIA_AREA',
               'JAPAN__':'JAPAN',
               'JAPAN_':'JAPAN',
               'LATIN AMERICA':'LATIN AMERICA',
               'ROK_AREA':'ROK_AREA',
               'US COMMERCIAL':'US COMMERCIAL',
               'USC':'US COMMERCIAL',
               'US COMMERICAL':'US COMMERCIAL',
               'US PUBLIC SECTOR':'US PS MARKET SEGMENT',
               'US PS MARKET SEGMENT':'US PS MARKET SEGMENT',
               'US PS Market Segment':'US PS MARKET SEGMENT'        
                }

        self.smartsheet_client = Smartsheet(self.token)
        self.smartsheet_client.errors_as_exceptions(True)
        
        self.sheets_response = self.smartsheet_client.Sheets.list_sheets(include_all=True)
        self.sheets_response_status = self.sheets_response.request_response.status_code

        # The Bookings sheet portion 
        self.bookings_sheet_id = None # to hold the "Compass Bookings" sheet name/id
        for sheet in self.sheets_response.data:
            if sheet.name == "Compass Bookings":
                self.bookings_sheet_id = sheet.id

        # Bookings sheet response directive
        self.booking_sheet = self.smartsheet_client.Sheets.get_sheet(self.bookings_sheet_id) 
        self.booking_sheet_result = self.booking_sheet.to_dict()  #make the booking sheet a dict
        
        self.booking_sheet_column_map = {}

        for column in self.booking_sheet_result['columns']:
            try:
                self.booking_sheet_column_map[column['title']] = column['id']
            except:
                print(column)
        
        self.booking_sheet_columns = list(self.booking_sheet_column_map.keys())

        self.booking_result_list_of_rows = []

        for row in self.booking_sheet_result['rows']:
            btempdf = pd.DataFrame(row['cells'], index = self.booking_sheet_columns)
            try:
                if 'value' in btempdf.columns:
                    self.booking_result_list_of_rows.append(btempdf['value'])
            except:
                print(btempdf.columns)
                print(btempdf)
        
        self.book_df = pd.concat(self.booking_result_list_of_rows, axis=1)
        self.book_dft = self.book_df.T
        self.book_dft.reset_index(drop=True, inplace=True)

        # Modify, Clean, & Transform Data in the DATAFRAME
        #self.book_dft['Customer Name'] = self.book_dft['Customer Name'].str.replace('* ','').str.replace('"','').str.replace('^_ ',' ').str.replace('&','and').str.upper()
        self.book_dft['Create Date'] = pd.to_datetime(self.book_dft['Create Date']).dt.date
        self.book_dft['Created'] = pd.to_datetime(self.book_dft['Created']).dt.date
        self.book_dft['Modified'] = pd.to_datetime(self.book_dft['Modified'], utc=False).dt.date
        self.book_dft['Date Readout Done'] = pd.to_datetime(self.book_dft['Date Readout Done']).dt.date
        self.book_dft['Date Completed'] = pd.to_datetime(self.book_dft['Date Completed']).dt.date
        self.book_dft['Lvl2 (Region)'] = self.book_dft['Lvl2 (Region)'].apply(self.get_right_theater)

        # Clean up and standardize the Sales Territory Level Fields
        self.book_dft['Lvl1'] = self.book_dft['Lvl1'].str.replace('__','')
        self.book_dft['Lvl1'] = self.book_dft['Lvl1'].str.upper()
        self.book_dft['Lvl2 (Region)'] = self.book_dft['Lvl2 (Region)'].str.upper()
        self.book_dft['Lvl3'] = self.book_dft['Lvl3'].str.upper()

        # Set the Target Fiscal fields to string types so that they correctly appear as discrete dimensions in Tableau
        self.book_dft['Target Fiscal Year'] = self.book_dft['Target Fiscal Year'].apply(self.convert_nan_to_int_to_str)
        self.book_dft['Target Fiscal Quarter'] = self.book_dft['Target Fiscal Quarter'].apply(self.convert_nan_to_int_to_str)
        self.book_dft['Target Fiscal Month'] = self.book_dft['Target Fiscal Month'].apply(self.convert_nan_to_int_to_str)
        #self.book_dft['Dupechk'] = 0

        # Set other data types and values as prescribed
        #self.book_dft['FINBI Booking'] = self.book_dft['FINBI Booking'].astype(float)
        self.book_dft['FINBI Fiscal WeekID'] = self.book_dft['FINBI Fiscal WeekID'].apply(self.convert_nan_to_int_to_str)
        self.book_dft['Deliverability'] = 'Good'
        self.book_dft['InsufficientDataCount'] = 0
        self.book_dft['Last Update'] = self.last_updated
#############################################################################################
        # The report sheets portion
        self.list_of_sheets_in_report = ["Compass Request Tracker - FY19Q4",
                                         "Compass Request Tracker - FY20Q1",
                                         "Compass Request Tracker - FY20Q2",
                                         "Compass Request Tracker - FY20Q3",
                                         "Compass Request Tracker - FY20Q4",
                                         "Compass Request Tracker"
                                         ]

        self.sheets_in_report_dict = {}
        
        for sheet in self.sheets_response.data:
            if sheet.name in self.list_of_sheets_in_report:
                self.sheets_in_report_dict[sheet.name] = sheet.id 

        # Report-specific response directives
        # Pull in a list of reports
        self.report_response = self.smartsheet_client.Reports.list_reports(include_all=True)
        # Status of the list of reports request
        self.report_response_status = self.report_response.request_response.status_code
        # Gets the data object portion of the reports response
        self.report = self.report_response.data 

        # Within the report data, find the Report ID for the report we want to use.
        self.report_id = [r.id for r in self.report if r.name == 'COMPASS Consolidated - Philip Shearin'][0]
        # Using the report ID, get all the records for the report we want to use
        self.report = self.smartsheet_client.Reports.get_report(self.report_id, page_size = self.pagesize, page = self.pagenum) 
        # Pass these records to a dict in order to build up a dataframe
        self.report_result = self.report.to_dict()

        # Begin building a DATAFRAME from the report results
        self.report_column_map = {}
        
        for column in self.report_result['columns']:
            self.report_column_map[column['title']] = column['virtualId']
        
        self.report_columns = list(self.report_column_map.keys())

        self.result_list = []

        for row in self.report_result['rows']:
            tempdf = pd.DataFrame(row['cells'], index = self.report_columns)
            try:
                if 'value' in tempdf.columns:
                    self.result_list.append(tempdf['value'])
            except:
                print(tempdf.columns)
                print(tempdf)
        
        self.data_df = pd.concat(self.result_list, axis=1)
        self.data_dft = self.data_df.T
        self.data_dft.reset_index(drop=True, inplace=True)

        # Modify, Clean, & Transform Data in the DATAFRAME
        self.data_dft['Create Date'] = pd.to_datetime(self.data_dft['Create Date']).dt.date
        self.data_dft['Created'] = pd.to_datetime(self.data_dft['Created']).dt.date
        self.data_dft['Modified'] = pd.to_datetime(self.data_dft['Modified'], utc=False).dt.date
        self.data_dft['Date Readout Done'] = pd.to_datetime(self.data_dft['Date Readout Done']).dt.date
        self.data_dft['Date Completed'] = pd.to_datetime(self.data_dft['Date Completed']).dt.date
        


        self.data_dft['Lvl2 (Region)'] = self.data_dft['Lvl2 (Region)'].apply(self.get_right_theater)

        # Prepare the previously marked Duplicate Deal ID field by resetting to NULL
        self.data_dft.loc[self.data_dft['Forecast Stage']=='7 - Duplicate Request','Forecast Stage']=pd.NA

        """         # Sort the dataframe to determine which rows contain duplicate deal IDs
        self.data_dft['Dupechk'] = 0
        self.did_subset = self.data_dft[['Request ID','Customer Name', 'Deal ID','Forecast Stage']].copy()
        self.did_subset.sort_values(['Deal ID','Request ID'], ignore_index=False, inplace=True)
        self.did_subset['Dupechk'] = self.did_subset.duplicated(['Deal ID'], keep='first')
        self.did_subset['Dupechk'] = self.did_subset.apply(lambda x: self.update_did_dupechk(x['Deal ID'], x['Dupechk']), axis=1)
        self.change_index_list = list(self.did_subset.loc[(self.did_subset['Dupechk']==True) & ~(self.did_subset['Forecast Stage']=='5 - Closed Won')].index)

        # Set the duplicate deal ID values so that pipeline values are not duplicated
        self.data_dft.loc[self.data_dft.index.isin(self.change_index_list),'Dupechk'] = 1
        self.data_dft.loc[self.data_dft.index.isin(self.change_index_list),'Forecast Stage'] = '7 - Duplicate Request'
        self.data_dft.loc[self.data_dft.index.isin(self.change_index_list),'Forecast Status'] = pd.NA
        self.data_dft.loc[self.data_dft.index.isin(self.change_index_list),'Opportunity Name'] = pd.NA
        self.data_dft.loc[self.data_dft.index.isin(self.change_index_list),'Projected Booking ($,000)'] = pd.NA
        self.data_dft.loc[self.data_dft.index.isin(self.change_index_list),'Target Fiscal Month'] = pd.NA
        self.data_dft.loc[self.data_dft.index.isin(self.change_index_list),'Target Fiscal Quarter'] = pd.NA
        self.data_dft.loc[self.data_dft.index.isin(self.change_index_list),'Target Fiscal Year'] = pd.NA """

        # Clean up the Customer Name field
        #self.data_dft['Customer Name'] = self.data_dft['Customer Name'].str.replace('* ','').str.replace('"','').str.replace('^_ ',' ').str.replace('&','and').str.upper()

        # Clean up and standardize the Sales Territory Level Fields
        self.data_dft['Lvl1'] = self.data_dft['Lvl1'].str.replace('__','')
        self.data_dft['Lvl1'] = self.data_dft['Lvl1'].str.upper()
        self.data_dft['Lvl2 (Region)'] = self.data_dft['Lvl2 (Region)'].str.upper()
        self.data_dft['Lvl3'] = self.data_dft['Lvl3'].str.upper()

        # Set the Target Fiscal fields to string types so that they correctly appear as discrete dimensions in Tableau
        self.data_dft['Target Fiscal Year'] = self.data_dft['Target Fiscal Year'].apply(self.convert_nan_to_int_to_str)
        self.data_dft['Target Fiscal Quarter'] = self.data_dft['Target Fiscal Quarter'].apply(self.convert_nan_to_int_to_str)
        self.data_dft['Target Fiscal Month'] = self.data_dft['Target Fiscal Month'].apply(self.convert_nan_to_int_to_str)

        self.data_dft['FINBI Booking'] = pd.NA
        #self.data_dft['FINBI Booking'] = self.data_dft['FINBI Booking'].astype(float)
        self.data_dft['FINBI Fiscal WeekID'] = pd.NA
        self.data_dft['FINBI Fiscal WeekID'] = self.data_dft['FINBI Fiscal WeekID'].astype(str)


        self.data_dft['Deliverability'] = self.data_dft.apply(lambda x: self.set_deliverability(x['Tableau Project Name'], x['Tableau Project Name 1.0']), axis=1)
        self.data_dft['InsufficientDataCount'] = self.data_dft.apply(lambda x: self.set_deliverability_count(x['Tableau Project Name'], x['Tableau Project Name 1.0']), axis=1)
        self.data_dft['Last Update'] = self.last_updated

    def get_sheet_id_from_sheets(self, sheet_name):
        for sheet in self.sheets_response:
            if sheet.name == sheet_name:
                self.sheets_in_report_dict[sheet_name] = sheet.id
                return self.sheets_in_report_dict
            else:
                errmsg = f"Cannot find the sheet from this sheet_name: {sheet_name} \n"
                print(errmsg)
                raise Exception(errmsg)


    def get_sheets_in_report_dict(self):
        return self.sheets_in_report_dict


    def convert_nan_to_int_to_str(self, dataframe_cell):
        if pd.isnull(dataframe_cell):
            return pd.NA
        else:
            try:
                return str(int(dataframe_cell))
            except:
                return pd.NA
    

    def update_did_dupechk(self, did, dupechk):
        if pd.isnull(did):
            return False
        elif did == None:
            return False
        elif did in [-44444,99999,9999,22222]:
            return False
        else:
            return dupechk

    
    def get_right_theater(self, level2):
        #print(level2)
        if pd.isnull(level2) or level2=='nan' or level2==None:
            return None
        else:
            return self.region_dict.get(level2.upper(), None)
        

    def get_meridian(self, hour):
        if hour >= 12:
            return 'PM'
        else:
            return 'AM'

    def set_deliverability(self, tab_project_name_zed, tab_project_name_one):
        projectfieldzed = str(tab_project_name_zed)
        projectfieldone = str(tab_project_name_one)
        if projectfieldzed[:9].lower() == 'thank you' or projectfieldzed[:13].lower() == 'compass - 717' or projectfieldone[:9].lower() == 'thank you':
            return "Insufficient Data"
        else:
            return "Good"

    def set_deliverability_count(self, tab_project_name_zed, tab_project_name_one):
        projectfieldzed = str(tab_project_name_zed)
        projectfieldone = str(tab_project_name_one)
        if projectfieldzed[:9].lower() == 'thank you' or projectfieldzed[:13].lower() == 'compass - 717' or projectfieldone[:9].lower() == 'thank you':
            return 1
        else:
            return 0




    def get_report_dataframe(self):
        return self.data_dft

    def get_bookings_dataframe(self):
        return self.book_dft




def replace_element(m):
    a = None
    if pd.isnull(m):  # if did is null or nan
        return None
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
            a = m.replace('&','').replace('"','').replace(' ',',').replace('\n',',').split(',')
            return a
        except:
            import pdb; pdb.set_trace()
    else:
        return m

