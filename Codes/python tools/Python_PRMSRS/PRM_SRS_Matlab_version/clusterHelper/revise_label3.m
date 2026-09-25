function [kmeans_labels_revised, representative_spectral_revised] = revise_label3(kmeans_labels, representative_spectral, pair_matches)
kmeans_labels_revised = zeros(size(kmeans_labels));
representative_spectral_revised = zeros(size(representative_spectral));
max_label_number = max(pair_matches(:));
for i = 1: max_label_number
    idx = (kmeans_labels == pair_matches(i, 2));
    kmeans_labels_revised(idx) = pair_matches(i, 1);
    representative_spectral_revised(:, pair_matches(i, 1)) = representative_spectral(:, pair_matches(i, 2));
end
end