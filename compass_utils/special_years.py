import pandas as pd
import datetime as dt
from dateutil import rrule

startdate = dt.datetime(1999,1,1)
year_count = 51

rulelist = list(rrule.rrule(rrule.YEARLY, interval = 1, count=year_count, dtstart = startdate, bymonth=7, byweekday=rrule.SA(-1)))

years =[rulelist[i+1].year for i in range(0,year_count -1)]
weeks = [(rulelist[i+1] - rulelist[i]).days/7 for i in range(0,year_count - 1)]
y_w = zip(years,weeks) # zip the year and the number of weeks in it

year_weeks = pd.DataFrame(data = y_w, columns = ['years','weeks'])

special_years = list(year_weeks.loc[year_weeks['weeks']==53]['years'])

def get_special_years():
    return special_years

#print(special_years)

#print(get_special_years())