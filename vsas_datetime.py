import os
import shutil
from osgeo import ogr
# from geopy import distance
# from geopy.distance import geodesic as GD


data_dir = #TODO: Add Path
reference_dir = "{}\\Reference".format(data_dir)
source_data_dir = "{}\\Source_Data".format(data_dir)
wip_data_dir = "{}\\WIP_Data".format(data_dir)
ref_species = "{}\\Species 2.shp".format(reference_dir)
source_trip_details = "{}\\Trip details.shp".format(source_data_dir)

for source_file in os.listdir(source_data_dir):
    os.remove("{}\\{}".format(source_data_dir, source_file))
for reference_file in os.listdir(reference_dir):
    shutil.copy(src="{}\\{}".format(reference_dir, reference_file),
                dst="{}\\{}".format(source_data_dir, reference_file))

driver = ogr.GetDriverByName('ESRI Shapefile')

env_con_data_source = driver.Open(source_trip_details, 1) # 0 means read-only. 1 means writeable.
env_con_layer = env_con_data_source.GetLayer()

count = 0

for env_con_feature in env_con_layer:
    print("{:=^80}".format(count))
    env_con_date = env_con_feature.GetField("date")
    env_con_geom = env_con_feature.GetGeometryRef()
    env_con_yx = env_con_geom.GetY(), env_con_geom.GetX()
    if env_con_date is None:
        current_datetime = None
        closest_distance = None
        species_data_source = driver.Open(ref_species, 0) # 0 means read-only. 1 means writeable.
        species_layer = species_data_source.GetLayer()
        for species_feature in species_layer:
            species_date = species_feature.GetField("Date & Tim")
            species_geom = species_feature.GetGeometryRef()
            species_yx = species_geom.GetY(), species_geom.GetX()
            distance_between = env_con_geom.Distance(species_geom)
            if closest_distance is None:
                current_datetime = species_date
                closest_distance = distance_between
            else:
                if distance_between <= closest_distance:
                    current_datetime = species_date
                    closest_distance = distance_between
        print("Datetime: {}\n\tDistance:{}m".format(current_datetime, closest_distance))
        env_con_feature.SetField("date", current_datetime)
        env_con_layer.SetFeature(env_con_feature)

        species_layer.ResetReading()
    count = count + 1




env_con_layer.ResetReading()
