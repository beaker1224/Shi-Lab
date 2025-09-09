addpath('spontanenousRamanHelper');
[raw_wavenumber, raw_control_nerve_dataset, raw_control_neuron_dataset, raw_mutant_nerve_dataset, raw_mutant_neuron_dataset] = read_all_data(strcat(pwd, '\schizophrenia'));
lb = 700; ub = 1700; idx = (raw_wavenumber > lb) & (raw_wavenumber < ub);
[wavenumber, control_nerve_dataset, control_neuron_dataset, mutant_nerve_dataset, mutant_neuron_dataset] = process_all_rawdata(raw_wavenumber, raw_control_nerve_dataset, raw_control_neuron_dataset, raw_mutant_nerve_dataset, raw_mutant_neuron_dataset, idx);

% cardiolipin_reference_spectra
wavenumber_samples = wavenumber;
potential_shift = 100; window_size = window_estimation(wavenumber_samples, potential_shift);
[subtype_name, reference_spectra] = reference_signal2(wavenumber_samples, window_size);
cardiolipin_reference_spectra = squeeze(reference_spectra(4, :, :));

% similarity
control_nerve_similarity = max(control_nerve_dataset'*cardiolipin_reference_spectra, [], 2);
mutant_nerve_similarity = max(mutant_nerve_dataset'*cardiolipin_reference_spectra, [], 2);
p = ranksum(control_nerve_similarity, mutant_nerve_similarity);

data = [control_nerve_similarity; mutant_nerve_similarity];
label = [char(ones(numel(control_nerve_similarity), 1) * 'control'); char(ones(numel(mutant_nerve_similarity), 1) * 'mutant ')];
scatterlabel = [ones(numel(control_nerve_similarity), 1); 2*ones(numel(mutant_nerve_similarity), 1)];
scatterlabel = scatterlabel + (rand(size(scatterlabel)) - 0.5)/10;
figure('Units', 'inches', 'OuterPosition', [0.25 0.25 4 4]);
boxplot(data, label,'symbol','');
xlabel('treatment in brain nerve');
hold on
scatter(scatterlabel,data,'r','filled')
ylabel('similarity score');
ax = gca;
ax.XAxis.LineWidth = 2;
ax.YAxis.LineWidth = 2;
set(gca,'fontsize',12,'FontWeight','bold');
exportgraphics(gca, 'figures/demo_8.emf', 'Resolution', 2000);