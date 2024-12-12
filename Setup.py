import os
import shutil

cwd = os.getcwd()
test_data_dir = #TODO: Add Path to VSAS Direcotry
in_data_dir = '{}\\In_Data'.format(cwd)
out_data_dir = '{}\\Out_Data'.format(cwd)

files_in_tdd = os.listdir(test_data_dir)
shutil.rmtree(out_data_dir)
os.makedirs(out_data_dir)


isExist = os.path.exists(in_data_dir)
if not isExist:
    # Create a new directory because it does not exist
    os.makedirs(in_data_dir)
    print("The new directory is created!")
else:
    shutil.rmtree(in_data_dir)
    os.makedirs(in_data_dir)

for file_in_tdd in files_in_tdd:
    if file_in_tdd.startswith('Env_Conditions'):
        shutil.copyfile(src="{}\\{}".format(test_data_dir, file_in_tdd),
                        dst="{}\\{}".format(in_data_dir, file_in_tdd))
    elif file_in_tdd.startswith('Species 2'):
        shutil.copyfile(src="{}\\{}".format(test_data_dir, file_in_tdd),
                        dst="{}\\{}".format(in_data_dir, file_in_tdd))
    elif file_in_tdd.startswith('Trip details'):
        shutil.copyfile(src="{}\\{}".format(test_data_dir, file_in_tdd),
                        dst="{}\\{}".format(in_data_dir, file_in_tdd))
    else:
        pass
