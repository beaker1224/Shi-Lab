wavenumber = (700:1700);
filename = 'subtype_reference/lipid_subtype_CH_streching.xlsx';
lipid_subtype_signal = readmatrix(filename);
Cardiolipin_raw = eliminiate_nan(lipid_subtype_signal(:, 10: 11)); 
Cardiolipin = signal_normalization(Cardiolipin_raw, wavenumber);
plot(wavenumber,Cardiolipin, 'lineWidth', 2, 'Color', 'black');
xlim([700, 1700]);
set(gca,'XTick',[700:200:1700]);
ylim([0 0.2]);
set(gca,'YTick',[0:0.05:0.2]);
xlabel('Wavenumber (cm^{-1})');
ylabel('Intensity (au)');
title('Cardiolipin')
ax = gca;
ax.XAxis.LineWidth = 2; 
ax.YAxis.LineWidth = 2;
set(gca,'fontsize',16,'FontWeight','bold');
exportgraphics(gca, 'figure2/reference2.tiff', 'Resolution', 2000);