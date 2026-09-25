function folder_name = read_dir_name(folder)
folder_info = dir(folder);
validated_folder = cell(size(folder_info, 1), 1);
idx = 0;
for i = 1: size(folder_info, 1)
    if (folder_info(i).isdir == 0)
        continue;
    end
    if ((folder_info(i).name == ".") || (folder_info(i).name == ".."))
        continue;
    end
    idx = idx + 1;
    validated_folder{idx} = folder_info(i).name;
end
folder_name = string(validated_folder(1: idx));
end