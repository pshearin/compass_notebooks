
import numpy as np
import pandas as pd
import datetime as dt
import os
from compass_smartsheet import CompassSmartsheet
import cisco_fiscal_calendar as fc

def convert_nan_to_int_to_str(dataframe_cell):
        if pd.isnull(dataframe_cell):
            return pd.NA
        else:
            try:
                return str(int(dataframe_cell))
            except:
                return pd.NA
                
cs = CompassSmartsheet()

