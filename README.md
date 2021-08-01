### DividendCalendar

DividendCalendar is a simple Python script used to populate a dedicated Google Calendar
with ex-dividend dates of selected stocks. The [yfinance](https://github.com/ranaroussi/yfinance) 
package is leveraged to obtain the dividend information, and the Google Calendar API is obviously 
used to add calendar entries. Detailed information about the Google API for Python is available on 
the [Github repo](https://github.com/googleapis/google-api-python-client), but the official 
[Google API quickstart guide](https://developers.google.com/calendar/api/quickstart/python) is the
correct starting point for understanding the DividendCalendar script. 

OAuth 2.0 credentials must be used to create/delete calendar entries. These credentials (OAuth 
Client ID) are generated in the [Google Cloud Platform](https://console.cloud.google.com) console. 
A key limitation with the free tier is that the credentials lifetime is only 7 days. 

More details in preparation...