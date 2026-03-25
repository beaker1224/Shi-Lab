function [wavenumber, dataset] = rawdataprocess(raw_wavenumber, raw_dataset, idx)
wavenumber = raw_wavenumber(idx);
part_dataset = raw_dataset(idx, :);
normalized_dataset = (part_dataset - min(part_dataset))./(max(part_dataset) - min(part_dataset));
dataset = normalized_dataset./sqrt(sum(normalized_dataset.^2));
end