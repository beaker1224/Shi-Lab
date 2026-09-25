% need to run hippocampus example with cardiolipin channel, then extract
% the pixel with highest score as an example
clear;
srs5_hippocampus;

% extract the column and row index of score maps
% in this case: row_idx = 473; col_idx = 544;
images = raw_image;
[max_score, max_score_loc] = max(score_images(:));
[row_idx, col_idx] = ind2sub([size(images, 2), size(images, 3)], max_score_loc);
pixel_spectra = images(:, row_idx, col_idx);

% cardiolipin reference data from Spontaenous Raman Spectra
wavenumber_samples = 2596: 4: 3285;
filename = 'subtype_reference/lipid_subtype_CH_streching.xlsx';
lipid_subtype_signal = readmatrix(filename);
Cardiolipin_raw = eliminiate_nan(lipid_subtype_signal(:, 10: 11));

% normalized by maximum value in each set for visual purpose
temp = (pixel_spectra - min(pixel_spectra))./(max(pixel_spectra) - min(pixel_spectra));
temp = temp./sqrt(sum(temp.^2));
vis_pixel_spectra = temp;
vis_cardiolipin_spectra = signal_normalization(Cardiolipin_raw, wavenumber_samples);

figure('Units', 'inches', 'OuterPosition', [0.25 0.25 8 4])
plot(wavenumber_samples, vis_cardiolipin_spectra, 'lineWidth', 2);
hold on

wavenumber_pixel = linspace(3085, 2796, 82);
plot(wavenumber_pixel, vis_pixel_spectra, 'lineWidth', 2);
legend('Cardiolipin Reference Spectra', 'Spectra on a Single Pixel');
%legend('Cardiolipin Reference Spectra', 'Spectra on a Single Pixel', 'Position',[2.25 0.25 5 0.5]);
%xlim([Cardiolipin_raw(1, 1), Cardiolipin_raw(end, 1)]);
xlim([2596, 3285]);
xlabel('Wavenumber (cm^{-1})');
ylabel('Intensity (au)');
ax = gca;
ax.XAxis.LineWidth = 2;
ax.YAxis.LineWidth = 2;
set(gca,'fontsize',12,'FontWeight','bold');
exportgraphics(gca, 'figures/demo_1.emf', 'Resolution', 2000);
saveas(gcf,'figures/demo_1','fig');
