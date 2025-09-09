addpath('spontanenousRamanHelper');
[raw_wavenumber, raw_control_nerve_dataset, raw_control_neuron_dataset, raw_mutant_nerve_dataset, raw_mutant_neuron_dataset] = read_all_data(strcat(pwd, '\brain_dataset'));
lb = 600; ub = 3150; idx = (raw_wavenumber > lb) & (raw_wavenumber < ub);
[wavenumber, control_nerve_dataset, control_neuron_dataset, mutant_nerve_dataset, mutant_neuron_dataset] = process_all_rawdata(raw_wavenumber, raw_control_nerve_dataset, raw_control_neuron_dataset, raw_mutant_nerve_dataset, raw_mutant_neuron_dataset, idx);

figure('Units', 'inches', 'OuterPosition', [0.25 0.25 8 4]);
plot(wavenumber, mean(control_nerve_dataset, 2), 'lineWidth', 2);
hold on;
plot(wavenumber, mean(mutant_nerve_dataset, 2), 'lineWidth', 2);
xlim([lb, ub]); xlabel('Wavenumber (cm^{-1})'); ylabel('Intensity (au)');
ax = gca; ax.XAxis.LineWidth = 2; ax.YAxis.LineWidth = 2;
set(gca,'fontsize',12,'FontWeight','bold'); legend('control', 'mutant');
ylim([0, 0.25])
exportgraphics(gca, 'figures/demo_7.emf', 'Resolution', 2000);
