import os
import shutil
from osgeo import ogr
import csv

esas_data_dir = r"T:\Programme 072 Marine Monitoring\207 Seabird and Cetacean Monitoring Advice\Seabirds_and_Cetaceans\Seabirds\Seabirds at Sea"
driver = ogr.GetDriverByName('ESRI Shapefile')
header = ['NAME', 'YEAR', 'AOI', 'PROJECT', 'PARENT', 'FEATURE COUNT', 'DATETIME COUNT', 'DATE COUNT', 'NO DATETIME']
# cwd = os.getcwd()
cwd = "C:\\VSAS"
salvage_yard = "{}\\Data\\SalvageYard".format(cwd)
wip_dir = "{}\\Data\\WIP_Data".format(cwd)


if os.path.exists(salvage_yard):
    shutil.rmtree(salvage_yard)
if not os.path.exists(wip_dir):
    os.makedirs(wip_dir)

dirs_to_repair = []

with open('ESAS-VSAS_DatetimeIssueScoping.csv', 'w', encoding='UTF8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(header)
    for dirpath, dirnames, filenames in os.walk(esas_data_dir):
        for filename in [f for f in filenames if f.endswith("Trip details.shp")]:
            path = os.path.join(dirpath, filename)
            dataSource = driver.Open(path, 0)
            if dataSource is None:
                print('Could not open {}'.format(path))
            else:
                layer = dataSource.GetLayer()
                featureCount = layer.GetFeatureCount()
                for feature in layer:
                    date_field = feature.GetField("date")
                    date_time_split = str(date_field).split('T')
                    if len(date_time_split) == 2:
                        pass
                    elif len(date_time_split) == 1:
                        if date_field is None:
                            to_repair_dir = "{}\\{}".format(salvage_yard, dirpath[130:])
                            if not os.path.exists(to_repair_dir):
                                os.makedirs(to_repair_dir)
                                dirs_to_repair.append(to_repair_dir)
                            for vsas_file in os.listdir(dirpath):
                                vsas_src = "{}\\{}".format(dirpath, vsas_file)
                                vsas_dst = "{}\\{}".format(to_repair_dir, vsas_file)
                                if vsas_file.startswith('Species 2'):
                                    try:
                                        print("Copying {}..\n\tfrom {}...\n\tto {}...".format(vsas_file, vsas_src, vsas_dst))
                                        shutil.copy(src=vsas_src,
                                                    dst=vsas_dst)
                                    except FileNotFoundError:
                                        pass
                                elif vsas_file.startswith('Trip details'):
                                    print("Copying {}..\n\tfrom {}...\n\tto {}...".format(vsas_file, vsas_src, vsas_dst))
                                    try:
                                        shutil.copy(src=vsas_src,
                                                    dst=vsas_dst)
                                    except FileNotFoundError:
                                        pass
                                elif vsas_file.startswith('Env_Conditions'):
                                    print("Copying {}..\n\tfrom {}...\n\tto {}...".format(vsas_file, vsas_src, vsas_dst))
                                    try:
                                        shutil.copy(src=vsas_src,
                                                    dst=vsas_dst)
                                    except FileNotFoundError:
                                        pass
                                else:
                                    pass

print(dirs_to_repair)

for dir_to_repair in dirs_to_repair:
    trip_details = "{}\\Trip details.shp".format(dir_to_repair)
    print("Repairing {}".format(trip_details))
    species = "{}\\Species 2.shp".format(dir_to_repair)
    repaired_dir = "{}\\Repaired".format(dir_to_repair)
    if not os.path.exists(repaired_dir):
        os.makedirs(repaired_dir)

    for wip_file in os.listdir(wip_dir):
        os.remove("{}\\{}".format(wip_dir, wip_file))
    for file_to_repair in os.listdir(dir_to_repair):
        shutil.copy(src="{}\\{}".format(dir_to_repair, file_to_repair),
                        dst="{}\\{}".format(wip_dir, file_to_repair))
#
#     driver = ogr.GetDriverByName('ESRI Shapefile')
#
#     env_con_data_source = driver.Open(trip_details, 1) # 0 means read-only. 1 means writeable.
#     env_con_layer = env_con_data_source.GetLayer()
#
#     count = 0
#
#     for env_con_feature in env_con_layer:
#         print("{:=^80}".format(count))
#         env_con_date = env_con_feature.GetField("date")
#         env_con_geom = env_con_feature.GetGeometryRef()
#         env_con_yx = env_con_geom.GetY(), env_con_geom.GetX()
#         if env_con_date is None:
#             current_datetime = None
#             closest_distance = None
#             species_data_source = driver.Open(species, 0) # 0 means read-only. 1 means writeable.
#             species_layer = species_data_source.GetLayer()
#             for species_feature in species_layer:
#                 species_date = species_feature.GetField("Date & Tim")
#                 species_geom = species_feature.GetGeometryRef()
#                 species_yx = species_geom.GetY(), species_geom.GetX()
#                 distance_between = env_con_geom.Distance(species_geom)
#                 if closest_distance is None:
#                     current_datetime = species_date
#                     closest_distance = distance_between
#                 else:
#                     if distance_between <= closest_distance:
#                         current_datetime = species_date
#                         closest_distance = distance_between
#             print("Datetime: {}\n\tDistance:{}m".format(current_datetime, closest_distance))
#             env_con_feature.SetField("date", current_datetime)
#             env_con_layer.SetFeature(env_con_feature)
#
#             species_layer.ResetReading()
#         count = count + 1
#     env_con_layer.ResetReading()
#     # for wip_file in os.listdir(wip_dir):
#     #     shutil.copyfile(src="{}\\{}".format(wip_dir, wip_file),
#     #                     dst="{}\\{}".format(repaired_dir, file_to_repair))
#
#
#
