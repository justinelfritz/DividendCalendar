from __future__ import print_function
import datetime
import os
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import yfinance as yf
import numpy as np

def check_filter_symlist(input_list):    
    """Check if list of ticker symbols (function argument) is empty, if the list" 
       contains dtypes other than string, and if list contains duplicate entries. 
       Warn user if empty or if non-string elements are found. Filter out any 
       duplicate entries.
       
       Parameters: 
       input_list (list of string): list of ticker symbols
       
       Returns:
       out_list (list of string): list of valid ticker symbols
       
       """         
   
    symlist_bool = all(type(elem) is str for elem in input_list)
    
    if not input_list:
        print('Input list is empty.')
    
    if not symlist_bool:
        print('Non-string elements present in symlist.')
        print('Corrective action recommend.')
    
    # Replace duplicate tickers if present
    input_set=set(input_list)
    if(len(input_list) != len(input_set)):
        in_arr=np.array(input_list)
        out_list=np.unique(in_arr)
    else:
        out_list=input_list
        
    return out_list
######################
def batch_divide_symlist(input_list):
    """Convert master list of all ticker symbols into a list of smaller lists,
    whose calendar entries can be added and batch-executed in smaller chunks.
    This feature helps avoid the dreaded BrokenPipeError by reducing the number
    of API calls per request."""
    
    orig_length=len(input_list)
    batch_length=25

    list_of_lists = [input_list[x:x+batch_length] for x in range(0, orig_length-1, batch_length)]

    return list_of_lists
######################

def proc_creds(SCOPES):
    """The standard template for credentials validation and token creation
    for the Google Calendar API. See the quickstart guide at 
    https://developers.google.com/calendar/api/quickstart/python
    
    Parameters:
    SCOPES: list of permission scopes required.
    
    Returns:
    creds: credentials to pass to our API service.
    
    """
    
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'JUL29_credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds
##############################################
def del_events(calendar_id,svc):
    """Batch-deletes all entries from the specified calendar.
    
    Parameters: 
    calendar_id: Unique identifier for the calendar.
    svc: The Service managing our requests.  
    
    Returns:
    None
    
    """
    
    events_set = svc.events().list(calendarId=calendar_id, maxResults=1000, singleEvents=True, orderBy='startTime').execute()
    events = events_set.get('items', [])
    if not events:
        print('No events found in calendar. No deletions necessary.')
    if events:
        
        del_batch = svc.new_batch_http_request()      
        for event_k in events:
            del_batch.add(svc.events().delete(calendarId=calendar_id,eventId=event_k['id']))

        del_batch.execute()
    print('Events successfully deleted.')
    return
##############################################
def event_json(sym, div_yield, timestamp_start):
    """json creation function for one specific event. 
    
    Parameters:
    sym: Ticker symbol corresponding to the event being created.
    div_yield: Forward dividend % yield for the ticker.
    timestamp_start: Date string of the Ex-dividend date.
    
    Returns:
    event_dict: json file containing event data.
    
    """
    
    event_dict = {
        'summary': sym+" EX-DIV "+div_yield,
        'start': {
            'date':timestamp_start.strftime('%Y-%m-%d'),
            #'dateTime': ts_out.strftime('%Y-%m-%d'+'T09:00:00'),
            'timeZone': 'America/New_York',
            },
        'end': {
            'date':(timestamp_start+datetime.timedelta(days=1)).strftime('%Y-%m-%d'),
            #'dateTime': ts_out.strftime('%Y-%m-%d'+'T16:00:00'),
            'timeZone': 'America/New_York',
            },
        'recurrence': [],
        'attendees': [],
        'reminders': {
            'useDefault': False,
            'overrides': [
#                {'method': 'email', 'minutes': 24 * 60},
                {'method': 'popup', 'minutes': 16 * 60},
                        ],
                    },
                }
    return event_dict

##############################################
def put_events(calendar_id, svc, sym_list):
    """Batch-inserts all entries into the specified calendar. Requires 
    use of yfinance library returns. Avoids pipe and connection errors
    by sub-dividing the list of 
    
    Parameters: 
    calendar_id: Unique identifier for the calendar.
    svc: The Service managing our requests.  
    sym_list: list of ticker symbols (dtype string)
    
    Returns:
    None
    
    """
    
    for sub_list in sym_list:
        put_batch = svc.new_batch_http_request()    

        for symstr in sub_list:
            print('Creating event for ',symstr)
            yf_info=yf.Ticker(symstr).info  #this is valid, even if symstr is no good
            try:
                exdiv_posix=yf_info['exDividendDate']
                div_yield=yf_info['dividendYield']
                exdiv_date=datetime.date.fromtimestamp(exdiv_posix)            
                fwd_yield='{:8.2f}%'.format(100.*div_yield).strip(" ")          
                event = event_json(symstr, fwd_yield, exdiv_date)
                put_batch.add(svc.events().insert(calendarId=calendar_id, body=event))
            except (IndexError, TypeError, KeyError):
                print(symstr,': This ticker may be suspended, data unavailable. Skipping calendar entry for {:}.'.format(symstr))

        put_batch.execute()

    return
##############################################
def main():

    # check for credentials
    # If modifying these scopes, delete the file token.json.
    #SCOPES = ['https://www.googleapis.com/auth/calendar.readonly', 
    SCOPES = ['https://www.googleapis.com/auth/calendar.events']   #used for PUT request
    creds=proc_creds(SCOPES)

#    h = Http(proxy_info=ProxyInfo(socks.PROXY_TYPE_HTTP, "127.0.0.1", 1087))

    service = build('calendar', 'v3', credentials=creds)
    
    cal_id='ab5r7tfq9qg0u36o2ar42mt0gg@group.calendar.google.com'

    # delete existing events
    del_events(cal_id,service) 
    
    symlist=['ABBV','AEP','ALE','ALL','BKH','BMY','BOH','BPMP','C','CHCO','CSCO','DTE','ENB',\
             'EOD','ET','EPD','EVRG','EXR','HD','IBM','IDA','KMB','MMM','MRK','NWE','OKE',\
             'OMC','PEP','PFG','PNW','PRU','R','SAFT','SHLX','SJM','SRE','TD','USB','VLO',\
             'SUNS','SCM','ARCC','FDUS','GBDC','GLAD','BKCC','HTGC','TSLX','MVC','GAIN',\
             'WASH','APAM','XOM','CVX','BP','ABT','MAIN','PAA','PSEC','SPG','FLNG','IVR',\
             'ICAGY','RWT','MFA','TWO','NYMT','NRZ','O','RDS-B','T','LNN','PAGP','EME',\
             'PFLT','AINV','OXLC','FCRD','OCCI','OXSQ','FSK','ICMB','BANX','PTMN','NRGX',\
             'MRCC','NMFC','OFS','HRZN','TPVG','PNNT','CCAP','WHF','SLRC','GECC','TCPC',\
             'OCSL','OHAI','VZ','TGP','KMI','AGNC','VOD','ING','STT','BK','BLK','CFG','C',\
             'CINF','CME','AFL','ADP','IEP','CMI','BHP','SCCO','KL','AEM','PG','CLX','TSN',\
             'CL','QSR','MO','T','LUMN','JNJ','RHHBY','MRK','GSK','SAP','TXN','QCOM','INTC',\
             'MPLX','MMP','ATO','IRM','WPC','MITT','NLY'] 
    
    
    valid_symlist=check_filter_symlist(symlist)
    put_symlist=batch_divide_symlist(valid_symlist)

    if (len(put_symlist) > 0):
        put_events(cal_id, service, put_symlist)
        
##############################################

if __name__ == '__main__':
    main()
    
