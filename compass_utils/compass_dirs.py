
class CompassDirs:
    def __init__(self):
        self.BASE_COMPASS_TRACKER_BACKUP_DIR = r'C:\Users\phsheari\Documents\Compass Tracker Backups\''
        self.COMPASS_TRACKER_CLOSED_WON_DIR = r'C:\Users\phsheari\Documents\Compass Tracker Backups\CLOSED_WON\''
        self.BASE_SFDC_DIR = r'C:\Users\phsheari\Documents\SFDC'
        self.SFDC_FULL_EXPORT_DIR = self.BASE_SFDC_DIR + r'\FULL_EXPORT\''
        self.SFDC_DELTA_DEALID_EXPORT_DIR = self.BASE_SFDC_DIR + r'\DELTA DEALID EXPORT\''
        self.SFDC_HIST_DEALID_EXPORT_DIR = self.BASE_SFDC_DIR + r'\HISTORICAL DEALID EXPORT\''
        self.SFDC_PIPELINE_UPDATE_DIR = self.BASE_SFDC_DIR + r'\PIPELINE UPDATE\''
    
    def get_base_tracker_backup_dir(self):
        return self.BASE_COMPASS_TRACKER_BACKUP_DIR

    def get_compass_tracker_closed_won_dir(self):
        return self.COMPASS_TRACKER_CLOSED_WON_DIR
    
    def get_sfdc_full_export_dir(self):
        return self.SFDC_FULL_EXPORT_DIR

    def get_sfdc_historical_dealid_dir(self):
        return self.SFDC_HIST_DEALID_EXPORT_DIR
    
    def get_sfdc_delta_dealid_dir(self):
        return self.SFDC_DELTA_DEALID_EXPORT_DIR
    
    def get_pipeline_update_dir(self):
        return self.SFDC_PIPELINE_UPDATE_DIR