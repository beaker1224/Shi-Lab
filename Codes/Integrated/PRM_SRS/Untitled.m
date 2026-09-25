addpath('imageprocessHelper');
addpath('spectraprocessHelper');
addpath('subtype_reference');

foldername = "HCC1806";
[raw_image, err] = readOIRFolderImage(folder_name);
image = raw_image;
imwrite(image, strcat(HCC1806, '/out', '.tiff'));