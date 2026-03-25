function data = readImage(fileName)
addpath('bfmatlab');
% if the path is not absolute, i.e. it is inside of the subtype folder,
% please use the two lines of code below.

% currentFolder = pwd;
% imageName = strcat([currentFolder, '/', fileName]);

% If fileName is already absolute, just use it:
imageName = fileName;  
% Optionally, you can check for existence:
if ~isfile(imageName)
    error('File not found: %s', imageName);
end
temp = bfopen(imageName);
rawImageData = temp{1};
frame = size(rawImageData, 1);
temp = rawImageData{1, 1};
column = size(temp, 1);
row = size(temp, 2);
data = zeros(frame, row, column);
for i = 1: frame
    data(i, :, :) = rawImageData{i, 1};
end
end