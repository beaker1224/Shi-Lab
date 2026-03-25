function [wavenumber, control_nerve_dataset, control_neuron_dataset, mutant_nerve_dataset, mutant_neuron_dataset] = process_all_rawdata(raw_wavenumber, raw_control_nerve_dataset, raw_control_neuron_dataset, raw_mutant_nerve_dataset, raw_mutant_neuron_dataset, idx)
[~, control_dataset] = rawdataprocess(raw_wavenumber, raw_control_dataset, idx);
[wavenumber, mutant_dataset] = rawdataprocess(raw_wavenumber, raw_mutant_dataset, idx);
end