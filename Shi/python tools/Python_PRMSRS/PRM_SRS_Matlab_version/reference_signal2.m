function [subtype_name, reference_spectra] = reference_signal2(wavenumber_samples, window_size)
gaps = wavenumber_samples(2) - wavenumber_samples(1);
stack_size = numel(wavenumber_samples);
scan_size = window_size * 2 + 1;

first_serial_start = wavenumber_samples(1) - window_size * gaps;
first_serial_stop = first_serial_start + wavenumber_samples(end) - wavenumber_samples(1);

dataset_by_shift = cell(1, scan_size);
for i = 1: scan_size
    serial_start = first_serial_start + (i - 1) * gaps;
    serial_stop = first_serial_stop + (i - 1) * gaps;
    serial_wavenumber_samples = linspace(serial_start, serial_stop, stack_size);
    [subtype_name, dataset_by_shift{i}] = reference_signal3(serial_wavenumber_samples);
end

subtype_size = numel(subtype_name);

reference_spectra = zeros(subtype_size, stack_size, scan_size);
% 12 subtypes, 76 Raman shift, 9 slide window
for i = 1: scan_size % each subtype
    raman_shift_channels = dataset_by_shift{i};
    for j = 1: subtype_size % for a particular raman shift
        reference_spectra(j, :, i) = raman_shift_channels{j};
    end
end

end