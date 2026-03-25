addpath('baseline_correction');
addpath('spontanenousRamanHelper');
[raw_wavenumber, raw_control_nerve_dataset, raw_control_neuron_dataset, raw_mutant_nerve_dataset, raw_mutant_neuron_dataset] = read_all_data(strcat(pwd, '\brain_dataset'));
lb = 2700; ub = 3150; idx = (raw_wavenumber > lb) & (raw_wavenumber < ub);
[wavenumber, control_nerve_dataset, control_neuron_dataset, mutant_nerve_dataset, mutant_neuron_dataset] = process_all_rawdata(raw_wavenumber, raw_control_nerve_dataset, raw_control_neuron_dataset, raw_mutant_nerve_dataset, raw_mutant_neuron_dataset, idx);

% cardiolipin_reference_spectra
wavenumber_samples = wavenumber;
potential_shift = 100; window_size = window_estimation(wavenumber_samples, potential_shift);
[subtype_name, reference_spectra] = reference_signal2(wavenumber_samples, window_size);

for i = 1: numel(subtype_name)
    subtype_reference_spectra = squeeze(reference_spectra(i, :, :));
    % similarity
    control_neuron_similarity = max(control_neuron_dataset'*subtype_reference_spectra, [], 2);
    mutant_neuron_similarity = max(mutant_neuron_dataset'*subtype_reference_spectra, [], 2);
    p = ranksum(control_neuron_similarity, mutant_neuron_similarity);
    data = [control_neuron_similarity; mutant_neuron_similarity];
    label = [char(ones(numel(control_neuron_similarity), 1) * 'control'); char(ones(numel(mutant_neuron_similarity), 1) * 'FTLD   ')];
    scatterlabel = [ones(numel(control_neuron_similarity), 1); 2*ones(numel(mutant_neuron_similarity), 1)];
    scatterlabel = scatterlabel + (rand(size(scatterlabel)) - 0.5)/10;
    figure('Units', 'inches', 'OuterPosition', [0.25 0.25 4 4]);
    boxplot(data, label,'symbol','');
    xlabel('treatment in brain neuron');
    hold on
    scatter(scatterlabel,data,'r','filled')
    ylabel('similarity score');
    ax = gca;
    ax.XAxis.LineWidth = 2;
    ax.YAxis.LineWidth = 2;
    set(gca,'fontsize',12,'FontWeight','bold');
    exportgraphics(gca, strcat('figures/demo_6_neuron_', num2str(lb), '_', num2str(ub), '_', subtype_name(i), '_p_', num2str(p), '.tiff'), 'Resolution', 2000);
    saveas(gcf,strcat('figures/demo_6_neuron_', num2str(lb), '_', num2str(ub), '_', subtype_name(i)),'fig');
    datacell = cell(numel(data), 2); datacell(:, 1) = cellstr(label); datacell(:, 2) = num2cell(data);
    writecell(datacell, strcat('figures/demo_6_neuron_', num2str(lb), '_', num2str(ub), '_', subtype_name(i), '_p_', num2str(p), '.xlsx'))
end