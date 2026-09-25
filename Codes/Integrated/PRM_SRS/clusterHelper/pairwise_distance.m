function distance = pairwise_distance(a, b)
max_label_number = size(a, 2);
a_repmat = repmat(a', max_label_number, 1);
b_repmat = repelem(b', max_label_number, 1);
difference = sqrt(mean((a_repmat - b_repmat).^2, 2));
distance = reshape(difference, max_label_number, max_label_number);
end