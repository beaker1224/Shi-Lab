function file_name = read_all_file_name(path, is_nerve)
file_name = [];
for i = 1: numel(path)
    path_i = path(i);
    filename = read_file_name(path_i, is_nerve);
    file_name = vertcat(file_name, filename);
end
end