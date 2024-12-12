import os
import shutil
from subprocess import call
import ogr
import sys
import datetime

def add_timebins(in_data_dir, out_data_dir):

    is_exist = os.path.exists(out_data_dir)
    now = datetime.datetime.now()
    now_timestamp = now.strftime("%Y%m%d%H%M%S")

    if not is_exist:
        # Create a new directory because it does not exist
        os.makedirs(out_data_dir)
    validation_dir = "{}\\Validation_{}".format(out_data_dir, now_timestamp)
    to_be_valid_dir ="{}\\To be Validated".format(validation_dir)
    valid_exist = os.path.exists(validation_dir)
    if not valid_exist:
        os.makedirs(validation_dir)
        os.makedirs(to_be_valid_dir)
        os.makedirs("{}\\Validated".format(validation_dir))
        os.makedirs("{}\\Validation_failed".format(validation_dir))


    print("The new directory is created!")

    env_conditions_in_shp = None
    species_2_in_shp = None
    trip_in_shp = None
    for root, dirs, files in os.walk(in_data_dir, topdown=False):
        for name in files:
            if name == 'Env_Conditions.shp':
                env_conditions_in_shp = os.path.join(root, name)
            elif name == 'Species 2.shp':
                species_2_in_shp = os.path.join(root, name)
            elif name == 'Trip details.shp':
                trip_in_shp = os.path.join(root, name)
    # Creates a datasource from the inout shapefile.
    driver = ogr.GetDriverByName('ESRI Shapefile')
    data_source_env_con = driver.Open(env_conditions_in_shp, 1)  # 0 means read-only. 1 means writeable.
    data_source_spec_2_add_time_bin = driver.Open(species_2_in_shp, 1)  # 0 means read-only. 1 means writeable.

    lastEnvCondX = None
    lastEnvCondY = None
    lastSpeciesYearMonDayHrMin = None

    # Checks the data source has been correct created
    if data_source_env_con is None:
        print('Could not open {}'.format(env_conditions_in_shp))
        sys.exit(1)
    else:
        print('Opened {}'.format(env_conditions_in_shp))

        envCon_layer = data_source_env_con.GetLayer()
        featureCount = envCon_layer.GetFeatureCount()

        envCondYearMonDayHrMin = []
        lastEnvCondYearMonDay = ''
        rowNum = 0
        missingLocationVal = 0
        missingDateVal = 0

        # Loops through the Env_Conditions.shp shape, removing any data recorded in Aberdeen
        for spe2_feature in envCon_layer:

            thisEnvCondYearMonDay = str(spe2_feature.GetField("date")).replace('T', ' ')
            thisEnvCondX = spe2_feature.GetField("X")
            thisEnvCondY = spe2_feature.GetField("Y")
            if -3 < thisEnvCondX < -2 and 57.1 < thisEnvCondY < 57.2:
                envCon_layer.DeleteFeature(spe2_feature.GetFID())
                data_source_env_con.ExecuteSQL('REPACK ' + envCon_layer.GetName())
                data_source_env_con.ExecuteSQL('RECOMPUTE EXTENT ON ' + envCon_layer.GetName())
                print('MESSAGE: A test row (FID:{}) located at Aberdeen has been deleted - {}'.
                      format(spe2_feature.GetFID(), env_conditions_in_shp))
            else:
                # add an end of day row to the first day when there are more than 2 days in the survey.
                print("if lastEnvCondYearMonDay({}) < thisEnvCondYearMonDay({}) and rowNum({}) > 1"
                      .format(lastEnvCondYearMonDay, thisEnvCondYearMonDay, rowNum))
                if lastEnvCondYearMonDay < thisEnvCondYearMonDay[0:10] and rowNum > 1:
                    print(' MESSAGE: the survey data is for more than one day: ' + lastEnvCondYearMonDay + ' - '
                          + thisEnvCondYearMonDay)
                    if len(thisEnvCondYearMonDay[0:10]) > 1:
                        envCondYearMonDayHrMin.append([lastEnvCondYearMonDay + 'T23:59', lastEnvCondX, lastEnvCondY])

                if len(thisEnvCondYearMonDay) > 1:
                    envCondYearMonDayHrMin.append([thisEnvCondYearMonDay[0:16], thisEnvCondX, thisEnvCondY])
                else:
                    missingDateVal = 1
                lastEnvCondYearMonDay = thisEnvCondYearMonDay[0:10]
                lastEnvCondX = thisEnvCondX
                lastEnvCondY = thisEnvCondY
                rowNum += 1
    # SORT needed!
    print(' Count of environmental condition records (timeBins): ' + str(len(envCondYearMonDayHrMin)))
    for i in envCondYearMonDayHrMin:
        print("TimeBin: {}".format(i))
    # print('  first: ' + str(envCondYearMonDayHrMin[0][0]))
    # print('  last: ' + str(envCondYearMonDayHrMin[len(envCondYearMonDayHrMin)-1][0]))

    # Checks the data source has been correct created
    if data_source_spec_2_add_time_bin is None:
        print('Could not open {}'.format(species_2_in_shp))
        sys.exit(1)
    else:
        print('Opened {}'.format(species_2_in_shp))
        envCon_layer = data_source_spec_2_add_time_bin.GetLayer()

        # Creates time bin colum
        fieldDefn = ogr.FieldDefn('timeBin', ogr.OFTString)
        envCon_layer.CreateField(fieldDefn)

        speciesYearMonDayHrMin = []
        lastStartStop = ''
        lastRow = ''
        missingDateVal = 0
        # Loops through the Env_Conditions.shp shape, removing any data recorded in Aberdeen
        for spe2_feature in envCon_layer:
            thisEnvCondYearMonDay = str(spe2_feature.GetField("Date & Tim")).replace('T', ' ')
            thisEnvCondX = spe2_feature.GetField("X")
            thisEnvCondY = spe2_feature.GetField("Y")
            print('+++ ID: {} | Length: {}'.format(spe2_feature.GetFID(), len(speciesYearMonDayHrMin)))
            if -3 < thisEnvCondX < -2 and 57.1 < thisEnvCondY < 57.2:
                envCon_layer.DeleteFeature(spe2_feature.GetFID())
                print('MESSAGE: A test row (FID:{}) located at Aberdeen has been deleted - {}'
                      .format(spe2_feature.GetFID(), env_conditions_in_shp))
            else:
                try:
                    thisSpeciesYearMonDayHrMin = spe2_feature[4][0:16]  # row[1][0:16].
                except TypeError:
                    thisSpeciesYearMonDayHrMin = '0'
                species_name = spe2_feature[0]  # row[0]

                # If the species name is Start or Stop the script will process this differently
                if species_name == 'Start':
                    # Checks for missing Stop
                    if lastStartStop == 'Start':
                        print('  MESSAGE: missing Stop entry near ' + thisSpeciesYearMonDayHrMin)
                        if len(thisSpeciesYearMonDayHrMin) > 1:
                            speciesYearMonDayHrMin.append(['Stop', lastSpeciesYearMonDayHrMin])
                    # Else if there is a date value, append the Start value to the speciesYearMonDayHrMin list
                    if len(thisSpeciesYearMonDayHrMin) > 1:
                        speciesYearMonDayHrMin.append(['Start', thisSpeciesYearMonDayHrMin])
                    else:
                        print('  ERROR: missing date value for record: Start')
                        missingDateVal = 1
                    lastStartStop = 'Start'
                elif species_name == 'Stop':
                    # Checks for missing Stop
                    if len(thisSpeciesYearMonDayHrMin) > 1:
                        speciesYearMonDayHrMin.append(['Stop', thisSpeciesYearMonDayHrMin])
                    else:
                        print('  ERROR: missing date value for species record: Stop')
                    lastStartStop = 'Stop'
                else:
                    if lastStartStop == 'Stop':
                        print('  MESSAGE: missing Start entry near ' + thisSpeciesYearMonDayHrMin)
                        if len(thisSpeciesYearMonDayHrMin) > 1:
                            speciesYearMonDayHrMin.append(['Start', thisSpeciesYearMonDayHrMin])
                        else:
                            print('  ERROR: missing date value for record: species (A)')
                            missingDateVal = 1
                        lastStartStop = 'Start'
                    # test for empty dates
                    if len(thisSpeciesYearMonDayHrMin) > 1:
                        speciesYearMonDayHrMin.append([species_name, thisSpeciesYearMonDayHrMin])
                    else:
                        print('  ERROR: missing date value for record: species (B)')
                lastSpeciesYearMonDayHrMin = thisSpeciesYearMonDayHrMin

    print(' Count of species observations (includes start stop rows): ' + str(len(speciesYearMonDayHrMin)))
    list_lenght = len(speciesYearMonDayHrMin)
    list_third = int(list_lenght/3)
    list_sample = int(list_third/3)+2
    list_end_sample = list_lenght - list_sample

    list_count = 0
    for i in speciesYearMonDayHrMin:
        if list_count < list_sample:
            print("Start - {}".format(i))
        if list_third+list_sample > list_count > list_third:
            print("Mid - {}".format( i))
        if list_count > list_end_sample:
            print("End - {}".format(i))
        list_count = list_count + 1

    if missingDateVal == 1:
        print(' ERROR: thre are empty value(s) in the Species.shp date field. Either remove the row or enter an appropriate date value in the species.shp shapefile found in the "To be Validated" folder. Then run this script again.')


    ## Add the last element of the species array to the end of the Env_Obs array - the env_cond list needs an 'end of day' record.
    # The X and Y values are dummy values because they won't be used.
    envCondYearMonDayHrMin.append([speciesYearMonDayHrMin[len(speciesYearMonDayHrMin)-1][1], '0', '0'])

    print(' Count of environmental condition records (timeBins): ' + str(len(envCondYearMonDayHrMin)))
    print('  first: ' + str(envCondYearMonDayHrMin[0][0]))
    print('  last: ' + str(envCondYearMonDayHrMin[len(envCondYearMonDayHrMin)-1][0]))
    print("TIMEBINS: {}".format(envCondYearMonDayHrMin))


    ## Loop through the env_cond and species arrays and update the timeBin time of each species record to an env_cond timeBin.
    ## Add a 'no observation' row to the species shapefile where the species shp lacks an observation by minute.
    countSpeciesBin = 0
    countSpeciesBinNoObsv = 0
    timeBinCount = 0
    timeBinMinuteCount = 0
    lunchTime = 0
    envCondSpeciesMatch = 0
    lastEnvCondDay = ''
    lastEnvCondDayHrMins = 0
    lastEnvCondYearMonDayHrMin = ''
    isStartStop = ''

    fieldNamA = 'Number'
    fieldNamB = 'Number >9'
    fieldNamC = 'Date & Tim'
    fieldNamD = 'timeBin'
    fieldNamE = 'Distance'
    fieldNamF = 'species na'
    schema = []


    data_source_spec_2_assign_time_bin = driver.Open(species_2_in_shp, 1) # 0 means read-only. 1 means writeable.
    species_2_in_shp = '{}\\Species 2.shp'.format(in_data_dir)
    data_source_spec_2_assign_time_bin = driver.Open(species_2_in_shp, 1) # 0 means read-only. 1 means writeable.
    if data_source_spec_2_assign_time_bin is None:
        print('Could not open {}'.format((species_2_in_shp)))
    else:
        print('Opened {}'.format((species_2_in_shp)))

        timebins = envCondYearMonDayHrMin
        timebins_dt =[]
        for timebin in timebins:
            timebins_dt.append(datetime.datetime.strptime(timebin[0].replace('T', ' '), '%Y-%m-%d %H:%M'))
        timebin_count = 0
        s2_layer = data_source_spec_2_assign_time_bin.GetLayer()

        for spe2_feature in s2_layer:
            curSpeciesYearMonDayHrMin = str(spe2_feature.GetField('Date & Tim')[0:16]).replace('T', ' ')
            current_timebin_start = str(timebins[timebin_count][0]).replace('T', ' ')
            current_timebin_end = str(timebins[timebin_count+1][0]).replace('T', ' ')
            curSpeciesYearMonDayHrMin_dt = datetime.datetime.strptime(curSpeciesYearMonDayHrMin, '%Y-%m-%d %H:%M')
            current_timebin_start_dt = datetime.datetime.strptime(current_timebin_start, '%Y-%m-%d %H:%M')
            current_timebin_end_dt = datetime.datetime.strptime(current_timebin_end, '%Y-%m-%d %H:%M')

            if curSpeciesYearMonDayHrMin_dt in timebins_dt:
                print("\t0\t{} - Species Datetime: {} - Timebin: {}".format(spe2_feature.GetFID(),
                                                                            curSpeciesYearMonDayHrMin_dt,
                                                                            curSpeciesYearMonDayHrMin_dt))
                spe2_feature.SetField('timeBin', '{}:00'.format(str(curSpeciesYearMonDayHrMin_dt).replace(' ', 'T')))
                s2_layer.SetFeature(spe2_feature)

            else:
                if current_timebin_start_dt <= curSpeciesYearMonDayHrMin_dt <= current_timebin_end_dt:
                    print("\t1\t{} - Species Datetime: {} - Timebin: {}".format(spe2_feature.GetFID(),
                                                                                curSpeciesYearMonDayHrMin_dt,
                                                                                current_timebin_start_dt))
                    spe2_feature.SetField('timeBin', '{}:00'.format(str(current_timebin_start_dt).replace(' ', 'T')))
                    s2_layer.SetFeature(spe2_feature)
                else:
                    if curSpeciesYearMonDayHrMin_dt < current_timebin_start_dt:
                        print("\t2\t{} - Species Datetime: {} - Timebin: {}".format(spe2_feature.GetFID(),
                                                                                    curSpeciesYearMonDayHrMin_dt,
                                                                                    current_timebin_start_dt))
                        spe2_feature.SetField('timeBin', '{}:00'.format(str(current_timebin_start_dt).replace(' ', 'T')))
                        s2_layer.SetFeature(spe2_feature)

                    elif curSpeciesYearMonDayHrMin_dt >= current_timebin_end_dt:
                        print('')
                        print("\t3\t{} - Species Datetime: {} - Timebin: {}".format(spe2_feature.GetFID(),
                                                                                    curSpeciesYearMonDayHrMin_dt,
                                                                                    current_timebin_end_dt))
                        spe2_feature.SetField('timeBin', '{}:00'.format(str(current_timebin_end_dt).replace(' ', 'T')))
                        s2_layer.SetFeature(spe2_feature)
                        timebin_count = timebin_count + 1

                        countSpeciesBinNoObsv += 1

                    lastEnvCondDayHrMins += 1
                    timeBinMinuteCount += 1

            print("{:-^80}\n".format('End Loop'))

    print('Count of timeBins: ' + str(timeBinCount))

    for files in os.listdir(in_data_dir):
        filepath = "{}\\{}".format(in_data_dir, files)
        if os.path.isfile(filepath) is True:
            print(files)
            shutil.copyfile(src="{}\\{}".format(in_data_dir, files),
                            dst="{}\\{}".format(to_be_valid_dir, files))



if __name__ == '__main__':

    call(["python", "Setup.py"])

    data_in = #TODO: Add Path
    esas_dir = #TODO: Add Path

    add_timebins(in_data_dir=data_in,
                 out_data_dir=esas_dir)
