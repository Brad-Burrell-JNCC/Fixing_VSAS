# Name: VSAS_Salvager.py
# Author / Curator: Bradley Burrell - 202305-Current
# Description: This script with search out instances of the Trip details.shp within a parent directory. Then it will
#              then fix all Trip details.shp which are missing the "date" field. The Script does this by assign the
#              date of the closest Species 2.shp's "Date & Tim" field.

# REQUIREMENTS:
#  1. Python version 3.10
#  2. OGR

# CHANGELOG:

import os
import shutil
from osgeo import ogr
import datetime
import sys


def add_timebins(in_data_dir, out_data_dir, driver):
    """
    This
    :param in_data_dir:
    :param out_data_dir:
    :param driver:
    :return:
    """

    is_exist = os.path.exists(out_data_dir)
    now = datetime.datetime.now()
    now_timestamp = now.strftime("%Y%m%d%H%M%S")

    if not is_exist:
        # Create a new directory because it does not exist
        os.makedirs(out_data_dir)
    validation_dir = "{}\\Validation_{}".format(out_data_dir, now_timestamp)
    to_be_valid_dir = "{}\\To be Validated".format(validation_dir)
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
    data_source_env_con = driver.Open(env_conditions_in_shp, 1)  # 0 means read-only. 1 means writeable.
    data_source_spec_2_add_time_bin = driver.Open(species_2_in_shp, 1)  # 0 means read-only. 1 means writeable.

    last_env_cond_x = None
    last_env_cond_y = None
    last_species_year_mon_day_hr_min = None

    # Checks the data source has been correct created
    if data_source_env_con is None:
        print('Could not open {}'.format(env_conditions_in_shp))
        sys.exit(1)
    else:
        print('Opened {}'.format(env_conditions_in_shp))

        env_con_layer = data_source_env_con.GetLayer()

        env_cond_year_mon_day_hr_min = []
        last_env_cond_year_mon_day = ''
        row_num = 0
        missing_location_val = 0
        missing_date_val = 0

        # Loops through the Env_Conditions.shp shape, removing any data recorded in Aberdeen
        for spe2_feature in env_con_layer:
            this_env_cond_year_mon_day = str(spe2_feature.GetField("date")).replace('T', ' ')
            this_env_cond_x = spe2_feature.GetField("X")
            this_env_cond_y = spe2_feature.GetField("Y")
            print("{:+^80}".format("Datetime: {}".format(this_env_cond_year_mon_day)))
            print("{:+^80}".format("Env Co X: {}".format(this_env_cond_x)))
            print("{:+^80}".format("Env Co Y: {}".format(this_env_cond_y)))

            if -3 < this_env_cond_x < -2 and 57.1 < this_env_cond_y < 57.2:
                env_con_layer.DeleteFeature(spe2_feature.GetFID())
                data_source_env_con.ExecuteSQL('REPACK ' + env_con_layer.GetName())
                data_source_env_con.ExecuteSQL('RECOMPUTE EXTENT ON ' + env_con_layer.GetName())
                print('MESSAGE: A test row (FID:{}) located at Aberdeen has been deleted - {}'.
                      format(spe2_feature.GetFID(), env_conditions_in_shp))
            else:
                # add an end of day row to the first day when there are more than 2 days in the survey.
                print("if lastEnvCondYearMonDay({}) < thisEnvCondYearMonDay({}) and rowNum({}) > 1"
                      .format(last_env_cond_year_mon_day, this_env_cond_year_mon_day, row_num))
                if last_env_cond_year_mon_day < this_env_cond_year_mon_day[0:10] and row_num > 1:
                    print(' MESSAGE: the survey data is for more than one day: ' + last_env_cond_year_mon_day + ' - '
                          + this_env_cond_year_mon_day)
                    if len(this_env_cond_year_mon_day[0:10]) > 1:
                        env_cond_year_mon_day_hr_min.append([last_env_cond_year_mon_day + 'T23:59', last_env_cond_x,
                                                             last_env_cond_y])

                if len(this_env_cond_year_mon_day) > 1:
                    env_cond_year_mon_day_hr_min.append([this_env_cond_year_mon_day[0:16], this_env_cond_x,
                                                         this_env_cond_y])
                else:
                    missing_date_val = 1
                last_env_cond_year_mon_day = this_env_cond_year_mon_day[0:10]
                last_env_cond_x = this_env_cond_x
                last_env_cond_y = this_env_cond_y
                row_num += 1

    # SORT needed!
    print(' Count of environmental condition records (timeBins): ' + str(len(env_cond_year_mon_day_hr_min)))
    for i in env_cond_year_mon_day_hr_min:
        print("TimeBin: {}".format(i))
    # print('  first: ' + str(envCondYearMonDayHrMin[0][0]))
    # print('  last: ' + str(envCondYearMonDayHrMin[len(envCondYearMonDayHrMin)-1][0]))

    # Checks the data source has been correct created
    if data_source_spec_2_add_time_bin is None:
        print('Could not open {}'.format(species_2_in_shp))
        sys.exit(1)
    else:
        print('Opened {}'.format(species_2_in_shp))
        env_con_layer = data_source_spec_2_add_time_bin.GetLayer()

        # Creates time bin colum
        field_defn = ogr.FieldDefn('timeBin', ogr.OFTString)
        env_con_layer.CreateField(field_defn)

        species_year_mon_day_hr_min = []
        last_start_stop = ''
        last_row = ''
        missing_date_val = 0
        # Loops through the Env_Conditions.shp shape, removing any data recorded in Aberdeen
        for spe2_feature in env_con_layer:
            this_env_cond_year_mon_day = str(spe2_feature.GetField("Date & Tim")).replace('T', ' ')
            this_env_cond_x = spe2_feature.GetField("X")
            this_env_cond_y = spe2_feature.GetField("Y")
            print('+++ ID: {} | Length: {}'.format(spe2_feature.GetFID(), len(species_year_mon_day_hr_min)))
            if -3 < this_env_cond_x < -2 and 57.1 < this_env_cond_y < 57.2:
                env_con_layer.DeleteFeature(spe2_feature.GetFID())
                print('MESSAGE: A test row (FID:{}) located at Aberdeen has been deleted - {}'
                      .format(spe2_feature.GetFID(), env_conditions_in_shp))
            else:
                try:
                    this_species_year_mon_day_hr_min = spe2_feature[4][0:16]  # row[1][0:16].
                except TypeError:
                    this_species_year_mon_day_hr_min = '0'
                species_name = spe2_feature[0]  # row[0]

                # If the species name is Start or Stop the script will process this differently
                if species_name == 'Start':
                    # Checks for missing Stop
                    if last_start_stop == 'Start':
                        print('  MESSAGE: missing Stop entry near ' + this_species_year_mon_day_hr_min)
                        if len(this_species_year_mon_day_hr_min) > 1:
                            species_year_mon_day_hr_min.append(['Stop', last_species_year_mon_day_hr_min])
                    # Else if there is a date value, append the Start value to the speciesYearMonDayHrMin list
                    if len(this_species_year_mon_day_hr_min) > 1:
                        species_year_mon_day_hr_min.append(['Start', this_species_year_mon_day_hr_min])
                    else:
                        print('  ERROR: missing date value for record: Start')
                        missing_date_val = 1
                    last_start_stop = 'Start'
                elif species_name == 'Stop':
                    # Checks for missing Stop
                    if len(this_species_year_mon_day_hr_min) > 1:
                        species_year_mon_day_hr_min.append(['Stop', this_species_year_mon_day_hr_min])
                    else:
                        print('  ERROR: missing date value for species record: Stop')
                    last_start_stop = 'Stop'
                else:
                    if last_start_stop == 'Stop':
                        print('  MESSAGE: missing Start entry near ' + this_species_year_mon_day_hr_min)
                        if len(this_species_year_mon_day_hr_min) > 1:
                            species_year_mon_day_hr_min.append(['Start', this_species_year_mon_day_hr_min])
                        else:
                            print('  ERROR: missing date value for record: species (A)')
                            missing_date_val = 1
                        last_start_stop = 'Start'
                    # test for empty dates
                    if len(this_species_year_mon_day_hr_min) > 1:
                        species_year_mon_day_hr_min.append([species_name, this_species_year_mon_day_hr_min])
                    else:
                        print('  ERROR: missing date value for record: species (B)')
                last_species_year_mon_day_hr_min = this_species_year_mon_day_hr_min

    if len(species_year_mon_day_hr_min) == 0:
        pass
    else:

        print(' Count of species observations (includes start stop rows): ' + str(len(species_year_mon_day_hr_min)))
        list_lenght = len(species_year_mon_day_hr_min)
        list_third = int(list_lenght/3)
        list_sample = int(list_third/3)+2
        list_end_sample = list_lenght - list_sample

        list_count = 0
        for i in species_year_mon_day_hr_min:
            if list_count < list_sample:
                print("Start - {}".format(i))
            if list_third+list_sample > list_count > list_third:
                print("Mid - {}".format( i))
            if list_count > list_end_sample:
                print("End - {}".format(i))
            list_count = list_count + 1

        if missing_date_val == 1:
            print('ERROR: thre are empty value(s) in the Species.shp date field.')
            print('Either remove the row or enter an appropriate date value in the species.shp shapefile found in the '
                  '"To be Validated" folder. Then run this script again.')
        # Add the last element of the species array to the end of the Env_Obs array - the env_cond list needs an
        # 'end of day'  record.
        # The X and Y values are dummy values because they won't be used.
        print("="*10, [species_year_mon_day_hr_min[len(species_year_mon_day_hr_min)-1][1], '0', '0'])
        env_cond_year_mon_day_hr_min.append([species_year_mon_day_hr_min[len(species_year_mon_day_hr_min)-1][1], '0', '0'])

        print(' Count of environmental condition records (timeBins): ' + str(len(env_cond_year_mon_day_hr_min)))
        print('  first: ' + str(env_cond_year_mon_day_hr_min[0][0]))
        print('  last: ' + str(env_cond_year_mon_day_hr_min[len(env_cond_year_mon_day_hr_min)-1][0]))
        print("TIMEBINS: {}".format(env_cond_year_mon_day_hr_min))

        # Loop through the env_cond and species arrays and update the timeBin time of each species record to an env_cond
        # timeBin.
        # Add a 'no observation' row to the species shapefile where the species shp lacks an observation by minute.
        count_species_bin = 0
        count_species_bin_no_obsv = 0
        time_bin_count = 0
        time_bin_minute_count = 0
        lunch_time = 0
        env_cond_species_match = 0
        last_env_cond_day = ''
        last_env_cond_day_hr_mins = 0
        last_env_cond_year_mon_day_hr_min = ''
        is_start_stop = ''

        field_nam_a = 'Number'
        field_nam_b = 'Number >9'
        field_nam_c = 'Date & Tim'
        field_nam_d = 'timeBin'
        field_nam_e = 'Distance'
        field_nam_f = 'species na'
        schema = []

        data_source_spec_2_assign_time_bin = driver.Open(species_2_in_shp, 1) # 0 means read-only. 1 means writeable.
        species_2_in_shp = '{}\\Species 2.shp'.format(in_data_dir)
        data_source_spec_2_assign_time_bin = driver.Open(species_2_in_shp, 1) # 0 means read-only. 1 means writeable.
        if data_source_spec_2_assign_time_bin is None:
            print('Could not open {}'.format(species_2_in_shp))
        else:
            print('Opened {}'.format(species_2_in_shp))

            timebins = env_cond_year_mon_day_hr_min
            timebins_dt =[]
            for timebin in timebins:
                print(timebin[0].replace('T', ' '), '%Y-%m-%d %H:%M')
                timebins_dt.append(datetime.datetime.strptime(timebin[0].replace('T', ' '), '%Y-%m-%d %H:%M'))
            timebin_count = 0
            s2_layer = data_source_spec_2_assign_time_bin.GetLayer()

            for spe2_feature in s2_layer:
                cur_species_year_mon_day_hr_min = str(spe2_feature.GetField('Date & Tim')[0:16]).replace('T', ' ')
                current_timebin_start = str(timebins[timebin_count][0]).replace('T', ' ')
                current_timebin_end = str(timebins[timebin_count+1][0]).replace('T', ' ')
                cur_species_year_mon_day_hr_min_dt = datetime.datetime.strptime(cur_species_year_mon_day_hr_min,
                                                                                '%Y-%m-%d %H:%M')
                current_timebin_start_dt = datetime.datetime.strptime(current_timebin_start, '%Y-%m-%d %H:%M')
                current_timebin_end_dt = datetime.datetime.strptime(current_timebin_end, '%Y-%m-%d %H:%M')

                if cur_species_year_mon_day_hr_min_dt in timebins_dt:
                    print("\t0\t{} - Species Datetime: {} - Timebin: {}".format(spe2_feature.GetFID(),
                                                                                cur_species_year_mon_day_hr_min_dt,
                                                                                cur_species_year_mon_day_hr_min_dt))
                    spe2_feature.SetField('timeBin', '{}:00'.format(str(cur_species_year_mon_day_hr_min_dt).replace(' ',
                                                                                                                    'T')))
                    s2_layer.SetFeature(spe2_feature)

                else:
                    if current_timebin_start_dt <= cur_species_year_mon_day_hr_min_dt <= current_timebin_end_dt:
                        print("\t1\t{} - Species Datetime: {} - Timebin: {}".format(spe2_feature.GetFID(),
                                                                                    cur_species_year_mon_day_hr_min_dt,
                                                                                    current_timebin_start_dt))
                        spe2_feature.SetField('timeBin', '{}:00'.format(str(current_timebin_start_dt).replace(' ', 'T')))
                        s2_layer.SetFeature(spe2_feature)
                    else:
                        if cur_species_year_mon_day_hr_min_dt < current_timebin_start_dt:
                            print("\t2\t{} - Species Datetime: {} - Timebin: {}".format(spe2_feature.GetFID(),
                                                                                        cur_species_year_mon_day_hr_min_dt,
                                                                                        current_timebin_start_dt))
                            spe2_feature.SetField('timeBin', '{}:00'.format(str(current_timebin_start_dt).replace(' ',
                                                                                                                  'T')))
                            s2_layer.SetFeature(spe2_feature)

                        elif cur_species_year_mon_day_hr_min_dt >= current_timebin_end_dt:
                            print('')
                            print("\t3\t{} - Species Datetime: {} - Timebin: {}".format(spe2_feature.GetFID(),
                                                                                        cur_species_year_mon_day_hr_min_dt,
                                                                                        current_timebin_end_dt))
                            spe2_feature.SetField('timeBin', '{}:00'.format(str(current_timebin_end_dt).replace(' ', 'T')))
                            s2_layer.SetFeature(spe2_feature)
                            timebin_count = timebin_count + 1

                            count_species_bin_no_obsv += 1

                        last_env_cond_day_hr_mins += 1
                        time_bin_minute_count += 1

                print("{:-^80}\n".format('End Loop'))

        print('Count of timeBins: ' + str(time_bin_count))

        for files in os.listdir(in_data_dir):
            filepath = "{}\\{}".format(in_data_dir, files)
            if os.path.isfile(filepath) is True:
                print(files)
                shutil.copyfile(src="{}\\{}".format(in_data_dir, files),
                                dst="{}\\{}".format(to_be_valid_dir, files))


# Please paste the directory with all VSAS files that require fixing.
# esas_data_dir = input("Please enter Parent Directory for VASA: ")
esas_data_dir = r"C:\VSAS-Backup\VSAS"

# Delete Previous Runs
for dirpath, dirnames, filenames in os.walk(esas_data_dir):
    if dirpath.endswith('Repaired'):
        shutil.rmtree(dirpath)
    if dirpath.endswith('To_Be_Validated'):
        shutil.rmtree(dirpath)

# Create OGR Driver
shp_driver = ogr.GetDriverByName('ESRI Shapefile')

# Walks through all directories in the Parenr
for dirpath, dirnames, filenames in os.walk(esas_data_dir):
    # Loops through all filename searching for Trip details.shp
    for filename in [f for f in filenames if f.endswith("Trip details.shp")]:
        # Creates path and datasource for Trip details.shp
        trip_details_path = os.path.join(dirpath, filename)
        trip_detail_datasource = shp_driver.Open(trip_details_path, 0)
        # Checks if Trip details.shp can be opened
        if trip_detail_datasource is None:
            print('Could not open {}'.format(trip_details_path)) 
        else:
            # Creates Layer
            layer = trip_detail_datasource.GetLayer()
            # Loops through all the features
            for feature in layer:
                # Pull out and check to see if the date field is correctly populated, using the length og split stings
                date_field = feature.GetField("date")
                date_time_split = str(date_field).split('T')
                if len(date_time_split) == 2:
                    pass
                elif len(date_time_split) == 1:
                    # Copies the file needing repair to a new folder
                    print("{}  needs Repair....".format(trip_details_path))
                    repaired_dir = "{}\\{}".format(dirpath, "Repaired")
                    if not os.path.exists(repaired_dir):
                        print("\tRepair Dir Not found... Creating...")
                        os.makedirs(repaired_dir)
                    print("\tPopulating Repair Dir...")
                    for vsas_file in os.listdir(dirpath):
                        vsas_src = "{}\\{}".format(dirpath, vsas_file)
                        vsas_dst = "{}\\{}".format(repaired_dir, vsas_file)
                        if vsas_file.startswith('Trip details'):
                            print("\t\tCopying {}..\n\t\t\tfrom {}...\n\t\t\tto {}...".format(vsas_file, vsas_src,
                                                                                              vsas_dst))
                            shutil.copy(src=vsas_src,
                                        dst=vsas_dst)
                    # Creates Path and Datasource for Trip and species Shapefiles
                    repaired_source_trip_details = "{}\\{}".format(repaired_dir, 'Trip details.shp')
                    ref_species = "{}\\{}".format(dirpath, 'Species 2.shp')
                    # 0 means read-only. 1 means writeable.
                    trip_details_data_source = shp_driver.Open(repaired_source_trip_details, 1)
                    trip_details_layer = trip_details_data_source.GetLayer()

                    # Loops thought all features in in the trip Shapefile
                    for trip_details_feature in trip_details_layer:
                        # Pulls the date and geometry field
                        trip_details_date = trip_details_feature.GetField("date")
                        trip_details_geom = trip_details_feature.GetGeometryRef()
                        trip_details_yx = trip_details_geom.GetY(), trip_details_geom.GetX()
                        if trip_details_date is None:
                            current_datetime = None
                            closest_distance = None
                            # 0 means read-only. 1 means writeable.
                            species_data_source = shp_driver.Open(ref_species, 0)
                            try:
                                species_layer = species_data_source.GetLayer()
                                # Finds the closest species point
                                for species_feature in species_layer:
                                    species_date = species_feature.GetField("Date & Tim")
                                    species_geom = species_feature.GetGeometryRef()
                                    species_yx = species_geom.GetY(), species_geom.GetX()
                                    distance_between = trip_details_geom.Distance(species_geom)
                                    if closest_distance is None:
                                        current_datetime = species_date
                                        closest_distance = distance_between
                                    else:
                                        if distance_between <= closest_distance:
                                            current_datetime = species_date
                                            closest_distance = distance_between
                                print("Datetime: {}\n\tDistance:{}m".format(current_datetime, closest_distance))
                                # Updates the Datetime of the nearest point.
                                trip_details_feature.SetField("date", current_datetime)
                                trip_details_layer.SetFeature(trip_details_feature)

                                species_layer.ResetReading()
                                print("{:-^80}".format("REPAIRED"))
                            except AttributeError:
                                print("++++ LAYER NONE TYPE +++++\n+++++ Path: {} +++++".format(ref_species))
                    trip_details_layer.ResetReading()
                    to_be_validated = "{}\\Ready_to_TimeBin".format(dirpath)
                    if not os.path.exists(to_be_validated):
                        print("\tRepair Dir Not found... Creating...")
                        os.makedirs(to_be_validated)
                    for file_vasa in os.listdir(dirpath):
                        if file_vasa.startswith('Env_Conditions'):
                            shutil.copy(src="{}\\{}".format(dirpath, file_vasa),
                                        dst="{}\\{}".format(to_be_validated, file_vasa))
                        elif file_vasa.startswith('Species 2'):
                            shutil.copy(src="{}\\{}".format(dirpath, file_vasa),
                                        dst="{}\\{}".format(to_be_validated, file_vasa))
                    for file_repaired in os.listdir(repaired_dir):
                        if file_repaired.startswith('Trip details'):
                            shutil.copy(src="{}\\{}".format(repaired_dir, file_repaired),
                                        dst="{}\\{}".format(to_be_validated, file_repaired))
                    validated = "{}\\Validated".format(dirpath)
                    if not os.path.exists(to_be_validated):
                        print("\tRepair Dir Not found... Creating...")
                    add_timebins(in_data_dir=to_be_validated,
                                 out_data_dir=validated,
                                 driver=shp_driver)
        print("="*300)

print("\n\n{:80}".format("DONE"))
