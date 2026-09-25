function file_name = read_file_name(path, is_nerve)
if (is_nerve == true)
    control_path = strcat(path, '/Nerve sub/');
else
    control_path = strcat(path, '/Neuron sub/');
end
file_info = dir(fullfile(control_path, '*.txt'));
file_name = control_path + string([{file_info(:).name}]);
file_name = file_name';
end