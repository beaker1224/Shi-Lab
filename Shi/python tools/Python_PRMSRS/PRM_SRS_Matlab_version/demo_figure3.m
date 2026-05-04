wavenumber_samples = linspace(2796, 3085, 82);

filename = 'subtype_reference/lipid_subtype_CH_streching.xlsx';
lipid_subtype_signal = readmatrix(filename);

Cardiolipin_raw = eliminiate_nan(lipid_subtype_signal(:, 10: 11));
Cardiolipin = signal_normalization(Cardiolipin_raw, wavenumber_samples);

figure('Units', 'inches', 'OuterPosition', [0.25 0.25 4 4])
plot(Cardiolipin_raw(:, 1), Cardiolipin_raw(:, 2), 'lineWidth', 2);
xlim([Cardiolipin_raw(1, 1), Cardiolipin_raw(end, 1)]);
% xlim([2696, 3185])
xlabel('Raman Shift (cm^{-1})', 'FontSize', 12, 'FontWeight', 'bold');
ylabel('Intensity (au)', 'FontSize', 12, 'FontWeight', 'bold');
ax = gca;
ax.XAxis.LineWidth = 2;
ax.YAxis.LineWidth = 2;
set(gca,'fontsize',12,'FontWeight','bold');
exportgraphics(gca, 'cardiolipin_signal.emf', 'Resolution', 2000);