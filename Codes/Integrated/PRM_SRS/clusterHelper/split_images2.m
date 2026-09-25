function cell_group = split_images2(images, N)
% split images into k group
images_2D = reshape(images, size(images, 1), size(images, 2) * size(images, 3));
clusters = kmeans(images_2D', N, 'MaxIter', 1000, 'Replicates', 5);
cell_group = reshape(clusters, size(images, 2), size(images, 3));
end