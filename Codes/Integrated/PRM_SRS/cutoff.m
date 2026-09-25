function confusion_matrix = cutoff(subtype_name, reference_dataset)
subtype_size = size(reference_dataset, 1); %12
stack_size = size(reference_dataset, 2); %76
scan_size = size(reference_dataset, 3); %19
centered_shift = 0.5*(scan_size + 1);
signal = zeros(subtype_size, stack_size);
for i = 1: subtype_size
    signal(i, :) = reference_dataset(i, :, centered_shift);
end

confusion_matrix = zeros(subtype_size);
for i = 1: subtype_size % exp signal
    for j = 1: subtype_size % reference signal
        confusion_matrix(i, j) = max(signal(i, :)*squeeze(reference_dataset(j, :, :)));
    end
end
% pcolor(categorical(subtype_name), categorical(subtype_name), confusion_matrix);
% colormap(gray(256));colorbar();
% axis square
heatmap(subtype_name, subtype_name,confusion_matrix);colorbar();
end