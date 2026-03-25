function [dataset, wavenumber] = read_data(file_name)
lens = size(readmatrix(file_name(1)), 1);
dataset = zeros(lens, numel(file_name));
for i = 1: numel(file_name)
    data = readmatrix(file_name(i));
    if (size(data, 1) ~= lens)
        disp("warning: wavenumber does not match!");
    end
    dataset(:, i) = data(:, 2);
end
wavenumber = data(:, 1);
end