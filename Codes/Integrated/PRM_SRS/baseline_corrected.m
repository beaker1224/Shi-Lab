function corrected_dataset = baseline_corrected(dataset)
corrected_dataset = zeros(size(dataset));
for i = 1: size(dataset, 2)
    corrected_dataset(:, i) = dataset(:, i) - asysm(dataset(:, i), 1e7, 0.001, 2);
end
end