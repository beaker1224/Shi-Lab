function [wavenumber, control_nerve_dataset, control_neuron_dataset, mutant_nerve_dataset, mutant_neuron_dataset] = read_all_data(dataset_folder)
% folder struction
% - control
%   - Ctr15
%       - Nerve sub
%           - nerve-1 sub.txt
%       - Neuron sub
%   - Ctr365
% - mutant
% dataset_folder = 'brain_dataset';
% dataset_folder, is_control_group, is_nerve
control_nerve_file_name = read_file(dataset_folder, true, true);
control_neuron_file_name = read_file(dataset_folder, true, false);
mutant_nerve_file_name = read_file(dataset_folder, false, true);
mutant_neuron_file_name = read_file(dataset_folder, false, false);

[control_nerve_dataset, wavenumber] = read_data(control_nerve_file_name);
control_neuron_dataset = read_data(control_neuron_file_name);
mutant_nerve_dataset = read_data(mutant_nerve_file_name);
mutant_neuron_dataset = read_data(mutant_neuron_file_name);

control_nerve_dataset = baseline_corrected(control_nerve_dataset);
control_neuron_dataset = baseline_corrected(control_neuron_dataset);
mutant_nerve_dataset = baseline_corrected(mutant_nerve_dataset);
mutant_neuron_dataset = baseline_corrected(mutant_neuron_dataset);

end