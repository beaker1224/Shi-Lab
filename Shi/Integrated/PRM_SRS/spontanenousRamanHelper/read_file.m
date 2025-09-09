function file_name = read_file(dataset_folder, is_control, is_nerve)
if (is_control == true)
    folder = strcat(dataset_folder, '/control/');
else
    folder = strcat(dataset_folder, '/mutant/');
end
path = folder + read_dir_name(folder);
file_name = read_all_file_name(path, is_nerve);
end