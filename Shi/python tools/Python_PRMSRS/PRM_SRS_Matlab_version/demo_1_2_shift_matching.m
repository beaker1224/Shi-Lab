% flow chart on how our method works, need to run srs5_hippocampus.m first
% clear;
% srs5_hippocampus;

% cardiolipin_reference_spectra
wavenumber_samples = linspace(2796, 3085, 82);
potential_shift = 100; window_size = window_estimation(wavenumber_samples, potential_shift);
[subtype_name, reference_spectra] = reference_signal2(wavenumber_samples, window_size);
cardiolipin_reference_spectra = squeeze(reference_spectra(4, :, :));

% pixel spectra
images = raw_image;
[max_score, max_score_loc] = max(score_images(:));
[row_idx, col_idx] = ind2sub([size(images, 2), size(images, 3)], max_score_loc);
temp = flipud(images(:, row_idx, col_idx)); temp = (temp - min(temp))./(max(temp) - min(temp));
pixel_spectra = temp./sqrt(sum(temp.^2));

% relative shift compared to original spectra
gap = wavenumber_samples(2) - wavenumber_samples(1);
relative_shift = gap * (-window_size: window_size);

% matching score for different matching shift
matching_score = cardiolipin_reference_spectra'*pixel_spectra;
a = 1/10000;
penalty_score = a*relative_shift.^2;
score = max(matching_score - penalty_score', 0);
figure('Units', 'inches', 'OuterPosition', [0.25 0.25 8 4])
plot(relative_shift, matching_score, 'lineWidth', 2);
hold on
plot(relative_shift, penalty_score, 'lineWidth', 2);
hold on
plot(relative_shift, score, 'lineWidth', 2);
xlim([-100, 100]);
ylim([0, 1]);
xlabel('Relative Shift Compared to Experiment Measurement (cm^{-1})');
ylabel('Scores');
legend('matching score', 'penalty score', 'score', 'Location', 'best');

ax = gca;
ax.XAxis.LineWidth = 2;
ax.YAxis.LineWidth = 2;
set(gca,'fontsize',12,'FontWeight','bold');
exportgraphics(gca, 'figures/demo_1_2.emf', 'Resolution', 2000);
saveas(gca, 'figures/demo_1_2', 'fig');


% shift pixel spectral left 21.41 cm-1 index = 24
% shift pixel spectral right 21.41 cm-1 index = 36
% max shift index: 28
idx = 24; s = 30 - idx;
left_shift_car_spectra = cardiolipin_reference_spectra(:, idx);
figure('Units', 'inches', 'OuterPosition', [0.25 0.25 2 4]);
plot(wavenumber_samples - s*gap, left_shift_car_spectra, 'lineWidth', 2);
hold on
plot(wavenumber_samples - s*gap, pixel_spectra, 'lineWidth', 2);
xticks([2800 2900 3000]);
ax = gca;
ax.XAxis.LineWidth = 2;
ax.YAxis.LineWidth = 2;
set(gca,'fontsize',12,'FontWeight','bold');
exportgraphics(gca, 'figures/demo_1_2_left_shift.emf', 'Resolution', 2000);
saveas(gca, 'figures/demo_1_2_left_shift', 'fig');

idx = 28; s = 30 - idx;
best_shift_car_spectra = cardiolipin_reference_spectra(:, idx);
figure('Units', 'inches', 'OuterPosition', [0.25 0.25 2 4]);
plot(wavenumber_samples - s*gap, best_shift_car_spectra, 'lineWidth', 2);
hold on
plot(wavenumber_samples - s*gap, pixel_spectra, 'lineWidth', 2);
xticks([2800 2900 3000]);
ax = gca;
ax.XAxis.LineWidth = 2;
ax.YAxis.LineWidth = 2;
set(gca,'fontsize',12,'FontWeight','bold');
exportgraphics(gca, 'figures/demo_1_2_best_shift.emf', 'Resolution', 2000);
saveas(gca, 'figures/demo_1_2_best_shift', 'fig');

idx = 36; s = 30 - idx;
right_shift_car_spectra = cardiolipin_reference_spectra(:, idx);
figure('Units', 'inches', 'OuterPosition', [0.25 0.25 2 4]);
plot(wavenumber_samples - s*gap, right_shift_car_spectra, 'lineWidth', 2);
hold on
plot(wavenumber_samples - s*gap, pixel_spectra, 'lineWidth', 2);
xticks([2800 2900 3000]);
ax = gca;
ax.XAxis.LineWidth = 2;
ax.YAxis.LineWidth = 2;
set(gca,'fontsize',12,'FontWeight','bold');
exportgraphics(gca, 'figures/demo_1_2_right_shift.emf', 'Resolution', 2000);
saveas(gca, 'figures/demo_1_2_right_shift', 'fig');
