from datetime import date, timedelta
import datetime
import holidays

def working_days():
    it_holidays = holidays.IT()
    it_rm_holidays = holidays.country_holidays('IT', subdiv='RM')
    #it_holidays = it_holidays + it_rm_holidays
    
    start = date(2023, 6, 23)
    end = date(2023, 6, 26)
    
    #holidays = [date(2022, 3, 15),date(2022, 3, 16),date(2022, 3, 17),date(2022, 3, 18)]

    # get list of all days
    all_days = (start + timedelta(x+1) for x in range((end - start).days))
    my_days = [start , [start + timedelta(x+1) for x in range((end - start).days)]]
    
    print('your days')
    for day in all_days:
        print(day)
        
    print('my days')
    for day in my_days:
        print(day)
        
    print('23-06-2023' in it_holidays, '24-06-2023' in it_holidays, '25-06-2023' in it_holidays, '26-06-2023' in it_holidays,)
    
    print(date(2023,6,23).weekday(), date(2023,6,24).weekday(), date(2023,6,25).weekday(), date(2023,6,26).weekday(),)
# filter business days
    # weekday from 0 to 4. 0 is monday adn 4 is friday
    # increase counter in each iteration if it is a weekday
    #count = sum(1 for day in all_days if day.weekday() < 5 and day not in it_holidays and day in it_rm_holidays)
    #count = sum(1 for day in all_days if day.weekday() < 5 and day not in it_holidays)
    count = sum(1 for day in all_days if day.weekday() < 5)

    return count
    
#print(working_days())

def time(): 
        tot_seconds = 150000
        seconds = datetime.timedelta(seconds=tot_seconds).seconds
        return str(datetime.timedelta(seconds=seconds))
    
#print(time())

from holidays.utils import list_supported_countries
def working_days2(start, end, country='IT', location='RM'):
    countries = list_supported_countries()
    try:
        cities = countries[country]
        if location in cities:
            print('ok cities', location)
        else:
            print('city not found')
        my_holidays = holidays.country_holidays(country=country, subdiv=location, years= start.year)

        dates = []
        
        while start <= end:
            if start.weekday() <= 4 and start not in my_holidays:
                print(start.weekday())
                dates.append(start) 
            start = start + datetime.timedelta(days=1)
        print(dates)
        
    except Exception as e:
        print(e)
    
    
working_days2(country='IT',location = 'RM', start = date(2023, 6, 26), end = date(2023, 6, 29) )



#print(list_supported_countries())

