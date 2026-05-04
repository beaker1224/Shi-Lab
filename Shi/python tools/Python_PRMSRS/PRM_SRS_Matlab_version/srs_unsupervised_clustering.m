rng default
addpath('imageprocessHelper');
addpath('spectraprocessHelper');
addpath('clusterHelper');

base_folder = 'srs_image/';
output_folder = 'unsupervised_clusters/';
data_folder = 'fixed brain';
dataset_folder = strcat(base_folder, data_folder);
mkdir(strcat(output_folder, data_folder));

lists = dir(dataset_folder); folder_names = {lists(3: end).name}';
task_counts = numel(folder_names);
unsupervised_clusters_number = 8;
w = linspace(835,860,76);

% ctr365 special case!
kmeans_labels = cell(1, task_counts);
representative_spectral = cell(1, task_counts);

for i = 1: task_counts
    folder_name = strcat(dataset_folder, '/', folder_names{i});
    [image, err] = readOIRFolderImage(folder_name);
    images = image_normalization(image);
    splited_image = split_images2(images, unsupervised_clusters_number);
    kmeans_labels{i} = splited_image;
    lens = size(images, 1);
    reference_spectral = zeros(lens, unsupervised_clusters_number);
    for j = 1: unsupervised_clusters_number
        images_2D = reshape(images, size(images, 1), size(images, 2) * size(images, 3));
        labels_2D = reshape(splited_image, 1, size(splited_image, 1) * size(splited_image, 2));
        idx = (labels_2D == j);
        reference_spectral(:, j) = mean(images_2D(:, idx), 2);
        
    end
%     if size(reference_spectral, 1) > 50
%         reference_spectral = reference_spectral(end - 49: end, :);
%     end
    representative_spectral{i} = reference_spectral;
end

cmaps = [0, 0, 0;...
    0, 0, 1;...
    0, 1, 0;...
    1, 0, 0;...
    0, 1, 1;...
    1, 0, 1;...
    1, 1, 0;...
    0.5, 1, 1];

kmeans_labels_revised = cell(1, task_counts);
kmeans_labels_revised{1} = kmeans_labels{1};

representative_spectral_revised = cell(1, task_counts);
representative_spectral_revised{1} = representative_spectral{1};

for i = 2: task_counts
    a = representative_spectral{1};
    b = representative_spectral{i};
    distance = pairwise_distance(a, b);
    pair_matches = matchpairs(distance, 1000);
    [kmeans_labels_revised{i}, representative_spectral_revised{i}] = revise_label3(kmeans_labels{i}, representative_spectral{i}, pair_matches);
end

for i = 1: task_counts
    imwrite(label2rgb(kmeans_labels_revised{i}, cmaps), strcat(output_folder, data_folder, '/', folder_names{i}, '.tiff'));
end

for i = 1: task_counts
    figure(); 
    this_spectral = representative_spectral_revised{i};
    for j = 1: unsupervised_clusters_number
        plot(w, flipud(this_spectral(:, j)), 'Color', cmaps(j, :));
        hold on
    end
    f = gcf; exportgraphics(f, strcat(output_folder, data_folder, '/', folder_names{i}, '_spectra.tiff'),'Resolution', 300);
    %close all
end


