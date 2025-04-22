function srs5_image_generation(root_folder)
% srs5_image_generation Process OIR images in the specified folder
%   root_folder : full path to directory containing CH-zoom* subfolders

% Add required helper paths
addpath('imageprocessHelper');
addpath('spectraprocessHelper');
addpath('subtype_reference');

% Ensure folder string ends without file separator
if endsWith(root_folder, filesep)
    root_folder = root_folder(1:end-1);
end

% Generate list of subfolders named CH***_out
folder_names = folders_generation(root_folder);

% Create output base folder
output_folder = strcat(root_folder, '_out', filesep);
mkdir(output_folder);

% Precompute spectral parameters
wavenumber_samples = linspace(2700, 3120, 72);
potential_shift = 100;
window_size = window_estimation(wavenumber_samples, potential_shift);
[subtype_name, reference_spectra] = reference_signal2(wavenumber_samples, window_size);

% Loop through each CH subfolder
for i = 1:numel(folder_names)
    folder_name = folder_names{i};
    [~, leafName] = fileparts(folder_name);
    output_subfolder = fullfile(output_folder, leafName);
    mkdir(output_subfolder);

    [raw_image, err] = readOIRFolderImage(folder_name);
    images = raw_image;
    images_2D = reshape(images, size(images,1), size(images,2)*size(images,3));

    % Normalize spectra
    images_2D = (images_2D - min(images_2D,'all'))./(max(images_2D,'all') - min(images_2D,'all'));
    images_2D_norm = images_2D ./ vecnorm(images_2D);
    images_2D_norms = flipud(images_2D_norm)';

    % Compute subtype score for each pixel
    for j = 1:numel(subtype_name)
        reference_subtype = squeeze(reference_spectra(j,:,:));
        score_matching_value = images_2D_norms * reference_subtype;
        [score_matching_matrix, shift_matrix] = max(score_matching_value, [], 2);
        score_shift_penalty_matrix = penalty_on_shift(shift_matrix, window_size);
        score_matrix = max(score_matching_matrix + score_shift_penalty_matrix, 0);
        
        score_images = reshape(score_matrix, size(images,2), size(images,3));
        outFile = fullfile(output_subfolder, sprintf('%s_convolution_image.tiff', subtype_name{j}));
        imwrite(score_images, outFile);
    end
end
end
