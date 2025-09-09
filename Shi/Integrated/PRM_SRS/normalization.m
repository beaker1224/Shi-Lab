function normalized_dataset = normalization(dataset)
normalized_dataset = (dataset - min(dataset))./(max(dataset) - min(dataset));
normalized_dataset = normalized_dataset./sum(normalized_dataset) * size(dataset, 1);
end