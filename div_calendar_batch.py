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

def check_duplicates_fmt(input_list):
    """Checks if input_list is empty, contains correct element types, and if contains duplicates. Returns list of 3 bools. """
    
    if not input_list:
        empty_bool = True
    if input_list:
        empty_bool = False
        
    symlist_bool = all(type(elem) is str for elem in input_list)
    
    input_set=set(input_list)
    if(len(input_list)==len(input_set)):
        print('No duplicates found in Ticker symbol list.')
        print('-----')
        dupl_bool=False
    else:
        print('Duplicates found in Ticker symbol list.')
        print('Duplicate calendar entries will be created.')
        dupl_bool=True
        
    return [empty_bool, symlist_bool, dupl_bool]

def filter_symlist(input_list):
# detects duplicates in list of Ticker symbols, and returns list with those duplicates removed
    in_arr=np.array(input_list)
    out_list=np.unique(in_arr)
    return out_list

######################
def proc_creds(SCOPES):
    creds = None
#    print (os.getcwd())
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
                'JUL16_credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds
##############################################
def del_events(calendar_id,svc):
    
    events_set = svc.events().list(calendarId=calendar_id, maxResults=1000, singleEvents=True, orderBy='startTime').execute()
    events = events_set.get('items', [])
    if not events:
        print('No events found in calendar. Proceeding with event creation.')
    if events:
        
        del_batch = svc.new_batch_http_request()      
        for event_k in events:
            del_batch.add(svc.events().delete(calendarId=calendar_id,eventId=event_k['id']))
#        for event_k in events:
#            event_mem=service.events().get(calendarId=calendar_id,eventId=event_k['id']).execute()
#            print('Deleting event with eventId:',event_k['id'],event_mem['summary'])
#            print('Deleting event with eventId:',event_k['id'])
#            svc.events().delete(calendarId=calendar_id,eventId=event_k['id']).execute()

        del_batch.execute()
    print('Events deleted, proceeding with new EX-DIV event creation.')
    return
##############################################
def put_events(calendar_id, svc, sym_list):

    put_batch = svc.new_batch_http_request()    

    # all symstr have already been checked for <type> and not empty 
    for symstr in sym_list:
        print('Creating event for ',symstr)
        sym=yf.Ticker(symstr)  #this is valid, even if symstr is no good
        try:
            ts=sym.info['exDividendDate']
            if (sym.info['dividendYield']>0.00999):
                fwd_yield='{:8.2f}%'.format(100.*sym.info['dividendYield']).strip(" ")
            
                ts_out=datetime.datetime.utcfromtimestamp(ts)

                event = {
                    'summary': symstr+" EX-DIV "+fwd_yield,
                    'start': {
                    #                'date':ts_out.strftime('%Y-%m-%d'),
                        'dateTime': ts_out.strftime('%Y-%m-%d'+'T09:00:00'),
                        'timeZone': 'America/New_York',
                    },
                    'end': {
                    #                'date':ts_out.strftime('%Y-%m-%d'),
                        'dateTime': ts_out.strftime('%Y-%m-%d'+'T16:00:00'),
                        'timeZone': 'America/New_York',
                    },
                    'recurrence': [],
                    'attendees': [],
                    'reminders': {
                        'useDefault': False,
                        'overrides': [
                            {'method': 'email', 'minutes': 24 * 60},
                            {'method': 'popup', 'minutes': 24 * 60},
                        ],
                    },
                }
        
#                event =svc.events().insert(calendarId=calendar_id, body=event).execute()
                put_batch.add(svc.events().insert(calendarId=calendar_id, body=event))
#                print('Event created: %s' % (event.get('htmlLink')))
   
        except IndexError:
            print(symstr,': This ticker may be suspended, data unavailable. Skipping calendar entry for {:}.'.format(symstr))
        except TypeError:
            print(symstr,': This ticker may be suspended, data unavailable. Skipping calendar entry for {:}.'.format(symstr))
        except KeyError:
            print(symstr,': This ticker may be suspended, data unavailable. Skipping calendar entry for {:}.'.format(symstr))
            
    put_batch.execute()
    
##############################################
def main():

    # check for credentials
    # If modifying these scopes, delete the file token.json.
    SCOPES = ['https://www.googleapis.com/auth/calendar.readonly', 'https://www.googleapis.com/auth/calendar.events']
    creds=proc_creds(SCOPES)

    # start service
    service = build('calendar', 'v3', credentials=creds)
    cal_id='ab5r7tfq9qg0u36o2ar42mt0gg@group.calendar.google.com'

    # delete existing events
#    del_events(cal_id,service)

    # you can add duplicates here, and any/all will be filtered out before populating calendar events
    symlist=['ABBV','AEP','ALE','ALL','BKH','BMY','BOH','BPMP','C','CHCO','CSCO','DTE','ENB','EOD','EVRG','EXR','HD','IBM','IDA','KMB','MMM','MRK','NWE','OKE','OMC','PEP','PFG','PNW','PRU','R','SAFT','SHLX','SJM','SRE','TD','USB','VLO','WASH','APAM','XOM','CVX','BP','ABT','MAIN','PAA','PSEC','SPG','FLNG','IVR','ICAGY','RWT','MFA','TWO','NYMT','NRZ','O','RDS-B','T','LNN','PAGP','EME','PFLT','AINV','OXLC','FCRD','OCCI','OXSQ','FSK','ICMB','BANX','PTMN','NRGX','MRCC','NMFC','OFS','HRZN','TPVG','PNNT','CCAP','WHF','SLRC','GECC','TCPC','SUNS','SCM','ARCC','FDUS','GBDC','GLAD','BKCC','HTGC','TSLX','MVC','GAIN','OCSL','OHAI','VZ','TGP','EPD','KMI','AGNC','VOD','ING','STT','BK','BLK','CFG','C','CINF','CME','AFL','ADP','IEP','CMI','BHP','SCCO','KL','AEM','PG','CLX','TSN','CL','QSR','MO','T','LUMN','JNJ','RHHBY','MRK','GSK','SAP','TXN','QCOM','INTC','EPD','MPLX','MMP','ENB','ATO','IRM','WPC','VZ','VOD','MITT','NLY']
    
    [empt_,typ_,dupl_] = check_duplicates_fmt(symlist)
    
    #if dupl_:
    valid_symlist=filter_symlist(symlist)
    put_events(cal_id,service,valid_symlist[50:])
        

#    if ((not empt_) & typ_ & (not dupl_)):
#        put_events(cal_id,service,symlist)
                  

        
##############################################

if __name__ == '__main__':
    main()
    
