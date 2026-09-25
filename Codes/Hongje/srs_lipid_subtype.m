clear
addpath('imageprocessHelper');
addpath('spectraprocessHelper');
addpath('subtype_reference');


root_folder = "Mouse_Brain_Ctrl"; folder_names = folders_generation(root_folder); % output_folder = strcat(root_folder, '_output/'); 
output_folder = strcat(root_folder, "_out/"); mkdir(output_folder);

% Reference spectra
wavenumber_samples = linspace(2700, 3150, 76);
[subtype_name, reference_dataset] = reference_signal3(wavenumber_samples);

% SRS image
for i = 1: numel(folder_names)
    folder_name = folder_names{i}; output_subfolder = strcat(output_folder, folder_name); mkdir(output_subfolder);
    
    [raw_image, err] = readOIRFolderImage(folder_name);
    images = raw_image; 
    images = image_normalization(images);
    images_2D = reshape(images, size(images, 1), size(images, 2) * size(images, 3));
        
    % Only show the images of protein and lipid without processing(need to
    % know the sequence of the images
     protein_images = uint16(2^16*retrieve_image(images(37, :, :)));
     lipid_images = uint16(2^16*retrieve_image(images(44, :, :)));
     imwrite(protein_images, strcat(output_subfolder, '/protein_channel', '.tiff'));
     imwrite(lipid_images, strcat(output_subfolder, '/lipid_channel', '.tiff'));
    
    %Lipid subtype 
    images_2D_norm  = images_2D./sqrt(sum(images_2D.^2));
    correlations = zeros(1, size(images_2D, 2));
    for j = 1: numel(subtype_name)
        for k = 1: size(images_2D, 2)
            output_subfolder_subtype = output_subfolder;
            correlations(k) = max(conv(images_2D_norm(:, k), reference_dataset{j}));
        end
        corr_images = reshape(correlations, size(images, 2), size(images, 3));
        imwrite(corr_images, strcat(output_subfolder_subtype, '/', subtype_name{j}, '_convolution_image', '.tiff'));  
    end
end