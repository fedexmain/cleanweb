from datetime import datetime, timedelta

timepoint_bases = {'year':0, 'month':12, 'day':30, 'hour':24, 'minute':60, 'second':60}
def subtract_datetime(past_datetime, current_datetime):
    distance = {}
    distance['second']= current_datetime.second - past_datetime.second
    distance['minute']= current_datetime.minute - past_datetime.minute
    distance['hour']= current_datetime.hour - past_datetime.hour
    distance['day']= current_datetime.day - past_datetime.day
    distance['month']= current_datetime.month - past_datetime.month
    distance['year']= current_datetime.year - past_datetime.year

    return distance

def print_operation(past_datetime, current_datetime):
    #print()
    #print('past_datetime: ', past_datetime, '\n', 'current_datetime: ', current_datetime)
    #print()
    pass

def return_timepoints(distance):
    #Get all timepoint available to deal with distance dictionary
    timepoints = []
    for timepoint in distance:
        timepoints.append(timepoint)
    return timepoints

def operation_mode_is_future(past_datetime, current_datetime):
    distance=subtract_datetime(past_datetime, current_datetime)
    timepoints = return_timepoints(distance)
    future_datetime_operation = False
    #Detect type of operation if it's future datetime operation or past datetime operation
    for num in range(len(timepoints)):
        reverse_index_num = len(timepoints) - (num+1)
        if distance[timepoints[reverse_index_num]] > 0:
            break;
        if distance[timepoints[reverse_index_num]] < 0:
            future_datetime_operation = True
            break;
    return future_datetime_operation

def operation_mode_is_Now(past_datetime, current_datetime):
    pd=past_datetime
    cd=current_datetime
    mode = True
    #check for equality through all datetime main attr 
    #to confirm the mode is True 
    if pd.year!=cd.year:
        mode = False
    elif pd.month!=cd.month:
        mode = False
    elif pd.day!=cd.day:
        mode = False
    elif pd.hour!=cd.hour:
        mode = False
    elif pd.minute!=cd.minute:
        mode = False
    elif pd.second!=cd.second:
        mode = False

    return mode

def operation_mode_is_past(past_datetime, current_datetime):
    return (not operation_mode_is_future() and not operation_mode_is_Now())

def reset_oprtn_for_future(past_datetime, current_datetime):
    #If operation is a future datetime, Inter-change datetime argument for future datetime operation
    #to take place right.
    #print()
    #print('Adjusting argument to be suitable for future datetime distance handling')
    return current_datetime, past_datetime

def return_absolute_distance(distance):
    #Check distance value for negative eradication by subtracting their absolute value
    # from their timepoint modal/base number 
    #print()
    #print('Eradicating all distance negative values....')
    timepoints = return_timepoints(distance)
    for timepoint in timepoints:
        if distance[timepoint] < 0:

            #find capable next timepoint to activate present timepoint base number to eradicate 
            #negative value
            activator = 1
            base = timepoint_bases[timepoint]
            next_timepoint = timepoints[timepoints.index(timepoint) +1]
            #Get value from next higher base distance and convert it for lower base proper calculation
            #and make exception for year distance as shouldn't be deducted if not up to 1 as its 
            #...base is always active
            if next_timepoint != 'year' or (next_timepoint == 'year' and distance[next_timepoint] >0):
                distance[next_timepoint]-=activator
                base = timepoint_bases[timepoint] *activator

            distance[timepoint] =  base - abs(distance[timepoint])
            #print(timepoint, distance)
    return distance

def timepoint_distance_in_words(timepoint, distance_value):
    word = ''
    if distance_value > 1:
        word+=str(distance_value)+timepoint
        if distance_value >1:
            word+='s'
    elif distance_value == 1:
        if timepoint == 'hour':
            word+='an '+timepoint
        else:
            word+='a '+timepoint
    return word

def report_datetime_distance(distance, timepoint_mode):
    timepoints = return_timepoints(distance)
    report = ''

    if timepoint_mode in ['all', 'All','full','Full']:
        for num in range(len(timepoints)):
            reverse_index_num = len(timepoints) - (num+1)
            timepoint = timepoints[reverse_index_num]
            #Make a report
            if report != '':
                report+=', '
            distance_value=distance[timepoint]
            report+=timepoint_distance_in_words(timepoint, distance_value)
        if report=='':
            report='Just Now'

    elif '_TimepointRange' in timepoint_mode:
        timepoint_range = 1
        if int(timepoint_mode.replace('_TimepointRange','')):
            timepoint_range = int(timepoint_mode.replace('_TimepointRange',''))

        if type(timepoint_range) == type(1):
            timepoint_range=timepoint_range%len(timepoints)
            for num in range(timepoint_range):
                reverse_index_num = len(timepoints) - (num+1)
                timepoint = timepoints[reverse_index_num]
                #Make a report
                if report != '':
                    report+=', '
                distance_value=distance[timepoint]
                report+=timepoint_distance_in_words(timepoint, distance_value)
            if report=='':
                num=timepoint_range
                reverse_index_num = len(timepoints) - (num+1)
                timepoint = timepoints[reverse_index_num]
                #Make a report
                if report != '':
                    report+=', '
                distance_value=distance[timepoint]
                report+=timepoint_distance_in_words(timepoint, distance_value)

    elif distance.get(timepoint_mode):
        distance_value=distance[timepoint_mode]
        report+=timepoint_distance_in_words(timepoint_mode, distance_value)

    #detect highest base timepoint with value
    elif timepoint_mode in ['highest', 'latest']:
        for num in range(len(timepoints)):
            reverse_index_num = len(timepoints) - (num+1)
            timepoint = timepoints[reverse_index_num]
            if distance[timepoint] > 0:
                distance_value=distance[timepoint]
                report+=timepoint_distance_in_words(timepoint, distance_value)
                break;
            if timepoint == 'second':
                report+='Just Now'

    #calculate distance in a specific timepoint
    elif 'in_' in timepoint_mode:
        timepoint_to_calc_in = timepoint_mode[timepoint_mode.index('_')+1:]
        if timepoint_to_calc_in in timepoints:
            timepoint_to_calc_in_base = timepoint_bases[timepoint_to_calc_in]
            result = 0
            if timepoint_to_calc_in_base != 0:
                for num in range(len(timepoints)):
                    reverse_index_num = len(timepoints) - (num+1)
                    timepoint = timepoints[reverse_index_num]
                    if timepoint == timepoint_to_calc_in:
                        next_base = 1
                    else:
                        next_base = timepoint_bases[timepoints[reverse_index_num-1]]

                    result+= (result+distance[timepoint]) * next_base
                    if timepoint == timepoint_to_calc_in:
                        #print('Distance between datetime is', result, timepoint_mode, 'mode')
                        return result
            else:
                result = distance[timepoint_to_calc_in]
                #print('Distance between datetime is', result, timepoint_mode, 'mode')
                return result
        else:
            #print('Error: timepoint_to_calc_in not in timepoints!')
            return None

    #print('Distance between datetime is',report)
    #print('============================================================')
    return report

def distance_between_two_datetime(past_datetime, current_datetime):
    #Check and reset operation for future operation
    if operation_mode_is_future(past_datetime, current_datetime):
        past_datetime,current_datetime=reset_oprtn_for_future(past_datetime,current_datetime)
        #print_operation(past_datetime, current_datetime)
    distance=return_absolute_distance(subtract_datetime(past_datetime, current_datetime))
    return distance

def fromNow(past_datetime, timepoint_mode):
    distance = distance_between_two_datetime(past_datetime, datetime.utcnow())
    return report_datetime_distance(distance, timepoint_mode)
    
if __name__ == '__main__':
    import random
    quest = int(input('\nChoose type of input to run operation;\n1. Random Input \n2. User Input: '))
    if quest == 1:
        year = random.randrange(2000, datetime.utcnow().year)
        month = random.randrange(1, 12+1)
        hour = random.randrange(1, 24+1)
        day = random.randrange(1, 32+1)
        minute = random.randrange(1, 60+1)
        second = random.randrange(1, 60+1)
    else:
        year = int(input('\nEnter datetime year: '))
        month = int(input('Enter datetime month: '))
        day = int(input('Enter datetime day: '))
        hour = int(input('Enter datetime hour: '))
        minute = int(input('Enter datetime minute: '))
        second = int(input('Enter datetime second: '))
    print('\n')

    current_datetime = datetime.now()
    past_datetime = datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second)
    print('Processing...................')
    print('.............................\n')
    print('*Current: ',current_datetime)
    print('*Past: ',past_datetime)
    print('.............................\n')

    distance = subtract_datetime(past_datetime, current_datetime)
    #print('============================================================')
    print_operation(past_datetime, current_datetime)

    print()
    print('----------------------------------------------')
    print('----------Detecting Operation Mode------------')
    print('----------------------------------------------')
    mode=''
    if operation_mode_is_future(past_datetime, current_datetime):
        #print()
        print('The operation is a Future distance operation')
        #Reset operation value to fit for future operation
        past_datetime, current_datetime = reset_oprtn_for_future(past_datetime, current_datetime)
        print_operation(past_datetime,current_datetime)
        distance = subtract_datetime(past_datetime, current_datetime)
        print_operation(past_datetime, current_datetime)
        #print(distance)
        mode='Future Operation'
    elif operation_mode_is_Now(past_datetime, current_datetime):
        print('The operation is NOW distance operation')
        mode='Now Operation'
    else:
        print('The operation is a Past distance operation')
        mode='Past Operation'
    print('----------------------------------------------')

    distance = return_absolute_distance(distance)
    print()
    print('Actual Distance',distance)
    print(report_datetime_distance(distance, 'full'), f'as full distance for {mode+"mode"}')
    print(report_datetime_distance(distance, 'latest'), f'as latest distance for {mode+"mode"}')
    print(report_datetime_distance(distance, 'in_year'), f'year... in_year distance for {mode+"mode"}')
    print(report_datetime_distance(distance, 'in_month'), f'month... in_month distance for {mode+"mode"}')
    print(report_datetime_distance(distance, 'in_day'), f'day... in_day distance for {mode+"mode"}')
    print(report_datetime_distance(distance, 'in_hour'), f'hour... in_hour distance for {mode+"mode"}')
    print(report_datetime_distance(distance, 'in_minute'), f'minute... in_minute distance for {mode+"mode"}')
    print(report_datetime_distance(distance, 'in_second'), f'second... in_second distance for {mode+"mode"}')


