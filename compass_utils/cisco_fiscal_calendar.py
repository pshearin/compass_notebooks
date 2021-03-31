from dateutil.parser import parse
import datetime as dt
import numpy as np
import pandas as pd
from range_key_dict import RangeKeyDict

starttime = dt.datetime.now()

current_year = int(starttime.year)

#class CiscoFiscalPeriod:

###  Note: Cisco's fiscal year is 364 days normally. Every 6 years, their cycle adds an additional week, and their fiscal year becomes 371 days long.
###  The list named "special_years" below, lists the years which were lengthened from 364 days to 371 days.
### SETUP: ###

_reference_start_date = dt.date(1999,8,1)  #the start date of fiscal year 2000
#_reference_year = 2000
_reference_year_day_count = 364
_special_years_day_count = 371
_how_many_years_to_track = 5
_special_year_startyear = 2004

_special_year_endyear = current_year + _how_many_years_to_track

_special_years = [2004,2010,2016,2021,2027]

_years_list = list(range(2000,current_year + _how_many_years_to_track + 1,1))
#_day_count = None

def get_day_count_for_year(_years_list): #construct a dictionary of key = "year", value = "count of days in the year"
    _year_day_count = {}
    for year in _years_list:
        if year in _special_years:
            _day_count = 371
        else:
            _day_count = 364
        _year_day_count[year] = _day_count
        
    return _year_day_count


def construct_date_dict(_years_list,_reference_start_date):
    _dict_dates = {}
    j = 0
    for y in _years_list:
        k = 0
        for _ in range(1,_year_day_count[y]+1): #this range is a count of days in the fiscal year indicated in the dict "_year_day_count"
            k+=1
            _dict_dates[str(_reference_start_date + dt.timedelta(days=j))] = k
            j+=1
    
    return _dict_dates


def construct_fiscal_year_dict(_years_list,_reference_start_date):
    _dict_fiscalyear = {}
    j = 0
    for y in _years_list:
        for _ in range(1,_year_day_count[y]+1):     #this range is a count of days in the fiscal year indicated in the dict "year_day_count"
            _dict_fiscalyear[str(_reference_start_date + dt.timedelta(days=j))] = y
            j+=1
        
    return _dict_fiscalyear


### construct the quarter assignments
def construct_quarter_list(_years_list,_special_years):
    _quarter_list = []    # contains tuples for each permutation of (year, quarter, days in the quarter)
    for year in _years_list:
        for q in [1,2,3,4]:
            if year in _special_years and q == 3:
                fiscal_quarter = (year, q, (14*7))
            else:
                fiscal_quarter = (year, q, (13*7))
            _quarter_list.append(fiscal_quarter)
    
    return _quarter_list


_year_day_count = get_day_count_for_year(_years_list)
_dict_dates = construct_date_dict(_years_list,_reference_start_date)
_dict_fiscalyear = construct_fiscal_year_dict(_years_list,_reference_start_date)
_quarter_list = construct_quarter_list(_years_list,_special_years)

dates = _dict_dates.keys()
fiscalyears = _dict_fiscalyear.values()
daynumbers = _dict_dates.values()

# Construct a dataframe, starting with the date, its corresponding fiscal year, and the daynumber of the year
df = pd.DataFrame(list(zip(dates,fiscalyears,daynumbers)),columns=['date','fiscalyear','daynumber'])

#print(df.info())

# Build the quarters dataframe
df_quarter = pd.DataFrame(_quarter_list, columns=['fiscalyear','fiscalquarter','days_in_quarter'])

df_quarter_groupby = df_quarter.groupby(['fiscalyear'])['days_in_quarter'].cumsum()

tmp_q = pd.merge(df_quarter,df_quarter_groupby, left_on = df_quarter.index, right_on=df_quarter_groupby.index).drop(columns=['key_0']).rename(columns={'days_in_quarter_x':'days_in_quarter','days_in_quarter_y':'cume_days_in_quarter'})


gx_drop_columns = ['key_0','key_1','fiscalyear_y','fiscalquarter_y','days_in_quarter_y']
gx_rename_columns = {'fiscalyear_x':'fiscalyear','fiscalquarter_x':'fiscalquarter','days_in_quarter_x':'days_in_quarter','cume_days_in_quarter_x':'quarterdays_end','cume_days_in_quarter_y':'quarterdays_begin'}

gx = pd.merge(tmp_q,tmp_q,how = 'left', left_on = [tmp_q.fiscalyear,tmp_q.index], right_on = [tmp_q.fiscalyear,tmp_q.index+1]).drop(columns=gx_drop_columns).fillna(0).rename(columns=gx_rename_columns)

calendar_df = pd.merge(df,gx, how='left',left_on = [df.fiscalyear], right_on = [gx.fiscalyear])

calendar_df = calendar_df.loc[(calendar_df['daynumber'] > calendar_df['quarterdays_begin']) & (calendar_df['daynumber'] <= calendar_df['quarterdays_end'])].drop(columns=['fiscalyear_y','key_0']).rename(columns={'fiscalyear_x':'fiscalyear'})

#calendar_df.reset_index(inplace=True)

#calendar_df.info()

n_year_rkd_monthOfQtr = RangeKeyDict({
    (1, 29): 1,
    (29, 57): 2,
    (57, 92): 3,
    (92, 120): 1,
    (120, 148): 2,
    (148, 183): 3,
    (183, 211): 1,
    (211, 239): 2,
    (239, 274): 3,
    (274, 302): 1,
    (302, 330): 2,
    (330, 365): 3,      
    })

s_year_rkd_monthOfQtr = RangeKeyDict({
    (1, 29): 1,  ### All keys in the 2nd position are 1 greater than the actual day count because the range function is n + 1
    (29, 57): 2,
    (57, 92): 3,
    (92, 120): 1,
    (120, 148): 2,
    (148, 183): 3,
    (183, 218): 1,     # 5 weeks
    (218, 246): 2,     # 4 weeks
    (246, 281): 3,     # 5 weeks
    (281, 309): 1,
    (309, 337): 2,
    (337, 372): 3,      
    })

def get_monthOfQuarter(dataframe_row):
    if dataframe_row.fiscalyear in _special_years:
        return s_year_rkd_monthOfQtr[dataframe_row.daynumber]
    else:
        return n_year_rkd_monthOfQtr[dataframe_row.daynumber]


calendar_df['month_of_quarter'] = calendar_df.apply(get_monthOfQuarter, axis=1)

n_year_rkd_monthOfYear = RangeKeyDict({
    (1, 29): 1,
    (29, 57): 2,
    (57, 92): 3,
    (92, 120): 4,
    (120, 148): 5,
    (148, 183): 6,
    (183, 211): 7,
    (211, 239): 8,
    (239, 274): 9,
    (274, 302): 10,
    (302, 330): 11,
    (330, 365): 12,      
    })


s_year_rkd_monthOfYear = RangeKeyDict({
    (1, 29): 1,  ### All keys in the 2nd position are 1 greater than the actual day count because the range function is n + 1
    (29, 57): 2,
    (57, 92): 3,
    (92, 120): 4,
    (120, 148): 5,
    (148, 183): 6,
    (183, 218): 7,
    (218, 246): 8,
    (246, 281): 9,
    (281, 309): 10,
    (309, 337): 11,
    (337, 372): 12,      
    })

def get_monthOfFiscalYear(dataframe_row):
    if dataframe_row.fiscalyear in _special_years:
        return s_year_rkd_monthOfYear[dataframe_row.daynumber]
    else:
        return n_year_rkd_monthOfYear[dataframe_row.daynumber]  

calendar_df['month_of_fiscalyear'] = calendar_df.apply(get_monthOfFiscalYear, axis=1)


n_year_rkd_weekOfYear = RangeKeyDict({
    (1, 8): 1,      
    (8, 15): 2,
    (15, 22): 3,    
    (22, 29): 4,
    (29, 36): 5,    
    (35, 43): 6,
    (43, 50): 7,    
    (50, 57): 8,
    (57, 64): 9,    
    (64, 71): 10,
    (71, 78): 11,   
    (78, 85): 12,
    (85, 92): 13,   
    (92, 99): 14,
    (99, 106): 15,  
    (106, 113): 16,
    (113, 120): 17, 
    (120, 127): 18,
    (127, 134): 19, 
    (134, 141): 20,
    (141, 148): 21, 
    (148, 155): 22,
    (155, 162): 23, 
    (162, 169): 24,
    (169, 176): 25, 
    (176, 183): 26,
    (183, 190): 27, 
    (190, 197): 28,
    (197, 204): 29, 
    (204, 211): 30,
    (211, 218): 31, 
    (218, 225): 32,
    (225, 232): 33, 
    (232, 239): 34,
    (239, 246): 35, 
    (246, 253): 36,
    (253, 260): 37, 
    (260, 267): 38,
    (267, 274): 39, 
    (274, 281): 40,
    (281, 288): 41, 
    (288, 295): 42,
    (295, 302): 43, 
    (302, 309): 44,
    (309, 316): 45, 
    (316, 323): 46,
    (323, 330): 47, 
    (330, 337): 48,
    (337, 344): 49, 
    (344, 351): 50,
    (351, 358): 51, 
    (358, 365): 52   
    })


s_year_rkd_weekOfYear = RangeKeyDict({
    (1, 8): 1,      
    (8, 15): 2,
    (15, 22): 3,    
    (22, 29): 4,
    (29, 36): 5,    
    (35, 43): 6,
    (43, 50): 7,    
    (50, 57): 8,
    (57, 64): 9,    
    (64, 71): 10,
    (71, 78): 11,   
    (78, 85): 12,
    (85, 92): 13,   
    (92, 99): 14,
    (99, 106): 15,  
    (106, 113): 16,
    (113, 120): 17, 
    (120, 127): 18,
    (127, 134): 19, 
    (134, 141): 20,
    (141, 148): 21, 
    (148, 155): 22,
    (155, 162): 23, 
    (162, 169): 24,
    (169, 176): 25, 
    (176, 183): 26,
    (183, 190): 27, 
    (190, 197): 28,
    (197, 204): 29, 
    (204, 211): 30,
    (211, 218): 31, 
    (218, 225): 32,
    (225, 232): 33, 
    (232, 239): 34,
    (239, 246): 35, 
    (246, 253): 36,
    (253, 260): 37, 
    (260, 267): 38,
    (267, 274): 39, 
    (274, 281): 40,
    (281, 288): 41, 
    (288, 295): 42,
    (295, 302): 43, 
    (302, 309): 44,
    (309, 316): 45, 
    (316, 323): 46,
    (323, 330): 47, 
    (330, 337): 48,
    (337, 344): 49, 
    (344, 351): 50,
    (351, 358): 51, 
    (358, 365): 52,
    (365, 372): 53,
    })

def get_weekOfFiscalYear(dataframe_row):
    if dataframe_row.fiscalyear in _special_years:
        return s_year_rkd_weekOfYear[dataframe_row.daynumber]
    else:
        return n_year_rkd_weekOfYear[dataframe_row.daynumber]

calendar_df['week_of_fiscalyear'] = calendar_df.apply(get_weekOfFiscalYear, axis=1)

n_year_rkd_weekOfQtr = RangeKeyDict({
    (1, 8): 1,      
    (8, 15): 2,
    (15, 22): 3,    
    (22, 29): 4,
    (29, 36): 5,    
    (35, 43): 6,
    (43, 50): 7,    
    (50, 57): 8,
    (57, 64): 9,    
    (64, 71): 10,
    (71, 78): 11,   
    (78, 85): 12,
    (85, 92): 13,   
    (92, 99): 1,
    (99, 106): 2,  
    (106, 113): 3,
    (113, 120): 4, 
    (120, 127): 5,
    (127, 134): 6, 
    (134, 141): 7,
    (141, 148): 8, 
    (148, 155): 9,
    (155, 162): 10, 
    (162, 169): 11,
    (169, 176): 12, 
    (176, 183): 13,
    (183, 190): 1, 
    (190, 197): 2,
    (197, 204): 3, 
    (204, 211): 4,
    (211, 218): 5, 
    (218, 225): 6,
    (225, 232): 7, 
    (232, 239): 8,
    (239, 246): 9, 
    (246, 253): 10,
    (253, 260): 11, 
    (260, 267): 12,
    (267, 274): 13, 
    (274, 281): 1,
    (281, 288): 2, 
    (288, 295): 3,
    (295, 302): 4, 
    (302, 309): 5,
    (309, 316): 6, 
    (316, 323): 7,
    (323, 330): 8, 
    (330, 337): 9,
    (337, 344): 10, 
    (344, 351): 11,
    (351, 358): 12, 
    (358, 365): 13   
    })

s_year_rkd_weekOfQtr = RangeKeyDict({
    (1, 8): 1,      
    (8, 15): 2,
    (15, 22): 3,    
    (22, 29): 4,
    (29, 36): 5,    
    (35, 43): 6,
    (43, 50): 7,    
    (50, 57): 8,
    (57, 64): 9,    
    (64, 71): 10,
    (71, 78): 11,   
    (78, 85): 12,
    (85, 92): 13,   
    (92, 99): 1,
    (99, 106): 2,  
    (106, 113): 3,
    (113, 120): 4, 
    (120, 127): 5,
    (127, 134): 6, 
    (134, 141): 7,
    (141, 148): 8, 
    (148, 155): 9,
    (155, 162): 10, 
    (162, 169): 11,
    (169, 176): 12, 
    (176, 183): 13,
    (183, 190): 1, 
    (190, 197): 2,
    (197, 204): 3, 
    (204, 211): 4,
    (211, 218): 5, 
    (218, 225): 6,
    (225, 232): 7, 
    (232, 239): 8,
    (239, 246): 9, 
    (246, 253): 10,
    (253, 260): 11, 
    (260, 267): 12,
    (267, 274): 13, 
    (274, 281): 14,
    (281, 288): 1, 
    (288, 295): 2,
    (295, 302): 3, 
    (302, 309): 4,
    (309, 316): 5, 
    (316, 323): 6,
    (323, 330): 7, 
    (330, 337): 8,
    (337, 344): 9, 
    (344, 351): 10,
    (351, 358): 11, 
    (358, 365): 12,
    (365, 372): 13,
    })


# get the week of the fiscal quarter
def get_weekOfFiscalQuarter(dataframe_row):
    if dataframe_row.fiscalyear in _special_years:
        return s_year_rkd_weekOfQtr[dataframe_row.daynumber]
    else:
        return n_year_rkd_weekOfQtr[dataframe_row.daynumber]

calendar_df['week_of_fiscalquarter'] = calendar_df.apply(get_weekOfFiscalQuarter, axis=1)

#####################################################################
# Calculate the Week number (1-5) of the Fiscal Month
n_year_rkd_weekOfFiscalMonth = RangeKeyDict({
    (1, 8): 1,      
    (8, 15): 2,
    (15, 22): 3,    
    (22, 29): 4,
    (29, 36): 1,    
    (35, 43): 2,
    (43, 50): 3,    
    (50, 57): 4,
    (57, 64): 1,    
    (64, 71): 2,
    (71, 78): 3,   
    (78, 85): 4,
    (85, 92): 5,   
    (92, 99): 1,
    (99, 106): 2,  
    (106, 113): 3,
    (113, 120): 4, 
    (120, 127): 1,
    (127, 134): 2, 
    (134, 141): 3,
    (141, 148): 4, 
    (148, 155): 1,
    (155, 162): 2, 
    (162, 169): 3,
    (169, 176): 4, 
    (176, 183): 5,
    (183, 190): 1, 
    (190, 197): 2,
    (197, 204): 3, 
    (204, 211): 4,
    (211, 218): 1, 
    (218, 225): 2,
    (225, 232): 3, 
    (232, 239): 4,
    (239, 246): 1, 
    (246, 253): 2,
    (253, 260): 3, 
    (260, 267): 4,
    (267, 274): 5, 
    (274, 281): 1,
    (281, 288): 2, 
    (288, 295): 3,
    (295, 302): 4, 
    (302, 309): 1,
    (309, 316): 2, 
    (316, 323): 3,
    (323, 330): 4, 
    (330, 337): 1,
    (337, 344): 2, 
    (344, 351): 3,
    (351, 358): 4, 
    (358, 365): 5   
    })

s_year_rkd_weekOfFiscalMonth = RangeKeyDict({
    (1, 8): 1,      
    (8, 15): 2,
    (15, 22): 3,    
    (22, 29): 4,
    (29, 36): 1,    
    (35, 43): 2,
    (43, 50): 3,    
    (50, 57): 4,
    (57, 64): 1,    
    (64, 71): 2,
    (71, 78): 3,   
    (78, 85): 4,
    (85, 92): 5,   
    (92, 99): 1,
    (99, 106): 2,  
    (106, 113): 3,
    (113, 120): 4, 
    (120, 127): 1,
    (127, 134): 2, 
    (134, 141): 3,
    (141, 148): 4, 
    (148, 155): 1,
    (155, 162): 2, 
    (162, 169): 3,
    (169, 176): 4, 
    (176, 183): 5,
    (183, 190): 1, 
    (190, 197): 2,
    (197, 204): 3, 
    (204, 211): 4,
    (211, 218): 5, 
    (218, 225): 1,
    (225, 232): 2, 
    (232, 239): 3,
    (239, 246): 4, 
    (246, 253): 1,
    (253, 260): 2, 
    (260, 267): 3,
    (267, 274): 4, 
    (274, 281): 5,
    (281, 288): 1, 
    (288, 295): 2,
    (295, 302): 3, 
    (302, 309): 4,
    (309, 316): 1, 
    (316, 323): 2,
    (323, 330): 3, 
    (330, 337): 4,
    (337, 344): 1, 
    (344, 351): 2,
    (351, 358): 3, 
    (358, 365): 4,
    (365, 372): 5,
    })


# get the week of the fiscal month
def get_weekOfFiscalMonth(dataframe_row):
    if dataframe_row.fiscalyear in _special_years:
        return s_year_rkd_weekOfFiscalMonth[dataframe_row.daynumber]
    else:
        return n_year_rkd_weekOfFiscalMonth[dataframe_row.daynumber]

calendar_df['week_of_fiscalmonth'] = calendar_df.apply(get_weekOfFiscalMonth, axis=1)
#####################################################################################

# Install FINBI fiscal values for lookup ('fiscal year','fiscal quarter id','fiscal period id','fiscal week id')
# Since fiscal year, and "FINBI fiscal year" is the same thing, we'll leave it as just "fiscal year"
#
#

def make_finbi_fiscal_quarter_id(df_fiscal_year, df_fiscal_quarter):
    return   str(df_fiscal_year) + "Q" + str(df_fiscal_quarter)


def make_finbi_fiscal_period_id(df_fiscal_year, df_month_of_fiscal_year):
    # mofy = month of fiscal year
    if df_month_of_fiscal_year < 10:
        mofy = "0" + str(df_month_of_fiscal_year)
    else:
        mofy = str(df_month_of_fiscal_year)
    
    return int(str(df_fiscal_year) + mofy)


def make_finbi_fiscal_week_id(df_fiscal_year, df_month_of_fiscal_year, df_week_of_fiscal_month):
    # mofy = month of fiscal year
    if df_month_of_fiscal_year < 10:
        mofy = "0" + str(df_month_of_fiscal_year)
    else:
        mofy = str(df_month_of_fiscal_year)
    
    return int(str(df_fiscal_year) + mofy + str(df_week_of_fiscal_month))


calendar_df['finbi_fiscal_quarter_id'] = calendar_df.apply(lambda x: make_finbi_fiscal_quarter_id(x['fiscalyear'], x['fiscalquarter']), axis=1)

calendar_df['finbi_fiscal_period_id'] = calendar_df.apply(lambda x: make_finbi_fiscal_period_id(x['fiscalyear'], x['month_of_fiscalyear']), axis=1)

calendar_df['finbi_fiscal_week_id'] = calendar_df.apply(lambda x: make_finbi_fiscal_week_id(x['fiscalyear'], x['month_of_fiscalyear'], x['week_of_fiscalmonth']), axis=1)

#########################################################################################




calendar_df['report_week_of_quarter'] = calendar_df['week_of_fiscalquarter']

##########################################################################################

def date_to_index(datestr):
    try:
        d = parse(datestr)
        d = d.isoformat()[:10]
        return d
    except TypeError:
        d = dt.date.isoformat(datestr)[:10]
        return d


def get_calendar_dataframe():
    return calendar_df


def get_fiscal_year(input_a_date):
    if pd.isnull(input_a_date):
        return pd.NA
    else:
        strdate = str(date_to_index(input_a_date))            #dt.datetime.strptime(input_a_date, '%m/%d/%Y')
        thisdate = dt.date.fromisoformat(strdate)
        df_maxdate = pd.to_datetime(calendar_df.date.max())
        if thisdate > df_maxdate:
            print(f"The date queried is greater than the current maximum date: {df_maxdate}. Please input an earlier date.")
        else:
            try:
                checkyear = calendar_df.loc[calendar_df.date == strdate]['fiscalyear'].values[0]
                return str(checkyear)
            except IndexError:
                return pd.NA

def get_fiscal_quarter(input_a_date):
    if pd.isnull(input_a_date):
        return pd.NA
    else:
        strdate = str(date_to_index(input_a_date))            #dt.datetime.strptime(input_a_date, '%m/%d/%Y')
        thisdate = dt.date.fromisoformat(strdate)
        df_maxdate = pd.to_datetime(calendar_df.date.max())
        if thisdate > df_maxdate:
            print(f"The date queried is greater than the current maximum date: {df_maxdate}. Please input an earlier date.")
        else:
            try:
                checkquarter = calendar_df.loc[calendar_df.date == strdate]['fiscalquarter'].values[0]
                return str(checkquarter)
            except IndexError:
                return pd.NA


def get_fiscal_month(input_a_date):
    if pd.isnull(input_a_date):
        #print("Input date is NULL. Please check your input date.")
        return pd.NA
    else:
        strdate = str(date_to_index(input_a_date))            #dt.datetime.strptime(input_a_date, '%m/%d/%Y')
        thisdate = dt.date.fromisoformat(strdate)
        df_maxdate = pd.to_datetime(calendar_df.date.max())
        if thisdate > df_maxdate:
            print(f"The date queried, {thisdate}, is greater than the current maximum date of {df_maxdate}. Please input an earlier date.")
        else:
            try:
                checkmonth = calendar_df.loc[calendar_df.date == strdate]['month_of_fiscalyear'].values[0]
                if checkmonth < 10:
                    return "0" + str(checkmonth)
                else:
                    return str(checkmonth)
            except IndexError:
                return pd.NA


def get_fiscal_week_of_fiscal_month(input_a_date):
    if pd.isnull(input_a_date):
        #print("Input date is NULL. Please check your input date.")
        return pd.NA
    else:
        strdate = str(date_to_index(input_a_date))            #dt.datetime.strptime(input_a_date, '%m/%d/%Y')
        thisdate = dt.date.fromisoformat(strdate)
        df_maxdate = pd.to_datetime(calendar_df.date.max())
        if thisdate > df_maxdate:
            print(f"The date queried is greater than the current maximum date: {df_maxdate}. Please input an earlier date.")
        else:
            try:
                checkweek = calendar_df.loc[calendar_df.date == strdate]['week_of_fiscalmonth'].values[0]
                return str(checkweek)
            except IndexError:
                return pd.NA


def get_fiscal_week_of_fiscal_quarter(input_a_date):
    if pd.isnull(input_a_date):
        #print("Input date is NULL. Please check your input date.")
        return pd.NA
    else:
        strdate = str(date_to_index(input_a_date))            #dt.datetime.strptime(input_a_date, '%m/%d/%Y')
        thisdate = dt.date.fromisoformat(strdate)
        df_maxdate = pd.to_datetime(calendar_df.date.max())
        if thisdate > df_maxdate:
            print(f"The date queried is greater than the current maximum date: {df_maxdate}. Please input an earlier date.")
        else:
            try:
                checkweek = calendar_df.loc[calendar_df.date == strdate]['week_of_fiscalquarter'].values[0]
                return str(checkweek)
            except IndexError:
                return pd.NA



def get_fiscal_week_of_fiscal_year(input_a_date):
    if pd.isnull(input_a_date):
        #print("Input date is NULL. Please check your input date.")
        return pd.NA
    else:
        strdate = str(date_to_index(input_a_date))            #dt.datetime.strptime(input_a_date, '%m/%d/%Y')
        thisdate = dt.date.fromisoformat(strdate)
        df_maxdate = pd.to_datetime(calendar_df.date.max())
        if thisdate > df_maxdate:
            print(f"The date queried is greater than the current maximum date: {df_maxdate}. Please input an earlier date.")
        else:
            try:
                checkweek = calendar_df.loc[calendar_df.date == strdate]['week_of_fiscalyear'].values[0]
                return str(checkweek)
            except IndexError:
                return pd.NA




def make_reporting_week(df_finbi_fiscal_week_id):
    return calendar_df.loc[calendar_df['finbi_fiscal_week_id']==df_finbi_fiscal_week_id, 'week_of_fiscalquarter'].values[0]


def get_reporting_week(df_finbi_fiscal_week_id):
    return calendar_df.loc[calendar_df['finbi_fiscal_week_id']==df_finbi_fiscal_week_id, 'report_week_of_quarter'].values[0]

#print(calendar_df.info())
#print(get_fiscal_year('8/31/2023'))
#print(get_fiscal_quarter('8/31/2023'))

