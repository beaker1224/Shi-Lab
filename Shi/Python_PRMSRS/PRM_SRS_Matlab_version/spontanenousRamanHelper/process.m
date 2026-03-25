function processed_dataset = process(dataset)
processed_dataset = normalization(baseline_corrected(dataset));
end