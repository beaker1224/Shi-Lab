% plot all subtype lipid signal 
wavenumber_samples = 400: 4: 3150;

filename = 'subtype_reference/lipid_subtype.xlsx';
lipid_subtype_signal = readmatrix(filename);

PE_raw = eliminiate_nan(lipid_subtype_signal(:, 1: 2)); 
PE = signal_normalization(PE_raw, wavenumber_samples);

PLS_raw = eliminiate_nan(lipid_subtype_signal(:, 4: 5));
PLS = signal_normalization(PLS_raw, wavenumber_samples);

%Cholesterol_raw = eliminiate_nan(lipid_subtype_signal(:, 7: 8));
%Cholesterol = signal_normalization(Cholesterol_raw, wavenumber_samples);

Cholesterol_filename = "Cholesterol 30-3500 100amp-100%-30-2-100-300-2400.txt";
Cholesterol_raw = readmatrix(Cholesterol_filename);
Cholesterol = signal_normalization(Cholesterol_raw, wavenumber_samples);

Cholesterol_ester_filename = "Cholesterol ester sub.txt";
Cholesterol_ester_raw = readmatrix(Cholesterol_ester_filename);
Cholesterol_ester = signal_normalization(Cholesterol_ester_raw, wavenumber_samples);

Cardiolipin_raw = eliminiate_nan(lipid_subtype_signal(:, 10: 11)); 
Cardiolipin = signal_normalization(Cardiolipin_raw, wavenumber_samples);

Sphingosine_raw = eliminiate_nan(lipid_subtype_signal(:, 13: 14));
Sphingosine = signal_normalization(Sphingosine_raw, wavenumber_samples);

filename = 'subtype_reference/RNA data.xlsx';
rna_signal = readmatrix(filename);
WT_raw = rna_signal(:, 1: 2); 
WT = signal_normalization(WT_raw, wavenumber_samples);

MUT_raw = rna_signal(:, [1, 3]); 
MUT = signal_normalization(MUT_raw, wavenumber_samples);

load('additional_subtype.mat');
PC = signal_normalization(PC, wavenumber_samples);
PS = signal_normalization(PS, wavenumber_samples);
CDP_DG = signal_normalization(CDP_DG, wavenumber_samples);
Lyso_PA = signal_normalization(Lyso_PA, wavenumber_samples);
Lysyl_DG = signal_normalization(Lysyl_DG, wavenumber_samples);


dsgPI_raw = readmatrix('subtype_reference/2021-02-17 LIPID grating2400 Int100 Amp100 Acq30 Acc2 slit100 hole300 (bg sub)/1,2-Diacyl-sn-glycero-3-phospho-L-serine-sub bg.txt');
dsgPI = signal_normalization(dsgPI_raw, wavenumber_samples);
LaPI_raw = readmatrix('subtype_reference/2021-02-17 LIPID grating2400 Int100 Amp100 Acq30 Acc2 slit100 hole300 (bg sub)/L-a-phosphatidyl  inositol-sub bg.txt');
LaPI = signal_normalization(LaPI_raw, wavenumber_samples);
LaPG_raw = readmatrix('subtype_reference/2021-02-17 LIPID grating2400 Int100 Amp100 Acq30 Acc2 slit100 hole300 (bg sub)/L-a-phosphatidyl-DL-glycerol sodium salt-sub bg.txt');
LaPG = signal_normalization(LaPG_raw, wavenumber_samples);

LPA_raw = readmatrix('subtype_reference/2021-02-17 LIPID grating2400 Int100 Amp100 Acq30 Acc2 slit100 hole300 (bg sub)/Oleoyl-L-a-lysophosphatidic acid-sub bg.txt');
LPA = signal_normalization(LPA_raw, wavenumber_samples);
Phosphatidylcholine_raw = readmatrix('subtype_reference/2021-02-17 LIPID grating2400 Int100 Amp100 Acq30 Acc2 slit100 hole300 (bg sub)/Phosphatidylcholine-sub bg.txt');
Phosphatidylcholine = signal_normalization(Phosphatidylcholine_raw, wavenumber_samples);
TAG_raw = readmatrix('subtype_reference/2021-02-17 LIPID grating2400 Int100 Amp100 Acq30 Acc2 slit100 hole300 (bg sub)/TAG mix-sub bg.txt');
TAG = signal_normalization(TAG_raw, wavenumber_samples);

lipid_16_0_raw = readmatrix('lipid_16_0.txt');
lipid_16_0 = signal_normalization(lipid_16_0_raw, wavenumber_samples);

lipid_18_0_raw = readmatrix('lipid_18_0.txt');
lipid_18_0 = signal_normalization(lipid_18_0_raw, wavenumber_samples);

lipid_24_5_BG_raw = readmatrix('lipid_24_5_BG.txt');
lipid_24_5_BG = signal_normalization(lipid_24_5_BG_raw, wavenumber_samples);

DHA_omega_3_22_6_raw = readmatrix('DHA_omega_3_22_6.txt');
DHA_omega_3_22_6 = signal_normalization(DHA_omega_3_22_6_raw, wavenumber_samples);

omega_3_24_5_raw = readmatrix('omega_3_24_5.txt');
omega_3_24_5 = signal_normalization(omega_3_24_5_raw, wavenumber_samples);

C24_1_cera3_raw = readmatrix('C24_1_cera3.txt');
C24_1_cera3 = signal_normalization(C24_1_cera3_raw, wavenumber_samples);

C24_cera2_raw = readmatrix('C24_cera2.txt');
C24_cera2 = signal_normalization(C24_cera2_raw, wavenumber_samples);

C22_cera1_raw = readmatrix('C22_cera1.txt');
C22_cera1 = signal_normalization(C22_cera1_raw, wavenumber_samples);

PC_18_1_raw = readmatrix('PC 18-1.txt');
PC_18_1 = signal_normalization(PC_18_1_raw, wavenumber_samples);

PE_18_1_raw = readmatrix('PE 18-1.txt');
PE_18_1 = signal_normalization(PE_18_1_raw, wavenumber_samples);

Ceramide_18_1_12_0_raw = readmatrix('Ceramide 18-1&12-0.txt');
Ceramide_18_1_12_0 = signal_normalization(Ceramide_18_1_12_0_raw, wavenumber_samples);

deoxycer_18_1_24_1_raw = readmatrix('deoxycer 18,1_24,1.txt');
deoxycer_18_1_24_1 = signal_normalization(deoxycer_18_1_24_1_raw, wavenumber_samples);

deoxycer_18_1_16_0_raw = readmatrix('deoxycer 18,1_16,0.txt');
deoxycer_18_1_16_0 = signal_normalization(deoxycer_18_1_16_0_raw, wavenumber_samples);

deoxycer_dihydro_cer_18_0_14_0_raw = readmatrix('deoxy dihydro cer 18,0_14,0.txt');
deoxycer_dihydro_cer_18_0_14_0 = signal_normalization(deoxycer_dihydro_cer_18_0_14_0_raw, wavenumber_samples);

deoxycer_dihydro_cer_18_0_24_1_raw = readmatrix('deoxy dihydro cer 18,0_24,1.txt');
deoxycer_dihydro_cer_18_0_24_1 = signal_normalization(deoxycer_dihydro_cer_18_0_24_1_raw, wavenumber_samples);


subtype_name = ["PE", "PLS", "Cholesterol","Cholesterol_ester", "Cardiolipin", "Sphingosine" ...
                "WT", "MUT", "PC", "PS", "CDP_DG", "Lyso_PA", "Lysyl_DG", "dsgPI", "LaPI" ...
                "LaPG", "LPA", "Phosphatidylcholine", "TAG","lipid_16_0","lipid_18_0" ...
                "DHA_omega_3_22_6", "omega_3_24_5", "C24_1_cera3", "C24_cera2", "C22_cera1" ...
                "PC-18-1", "PE-18-1", "Ceramide-18-1-12-0", "deoxycer 18,1_24,1", "deoxycer 18,1_16,0" ...
                "deoxy dihydro cer 18,0_14,0", "deoxy dihydro cer 18,0_24,1"];
reference_dataset = {PE, PLS, Cholesterol, Cholesterol_ester, Cardiolipin, Sphingosine ...
                     WT, MUT, PC, PS, CDP_DG, Lyso_PA, Lysyl_DG, dsgPI, LaPI ...
                     LaPG, LPA, Phosphatidylcholine, TAG, lipid_16_0, lipid_18_0 ...
                     DHA_omega_3_22_6, omega_3_24_5, C24_1_cera3, C24_cera2, C22_cera1 ...
                     PC_18_1, PE_18_1, Ceramide_18_1_12_0, deoxycer_18_1_24_1, deoxycer_18_1_16_0 ...
                     deoxycer_dihydro_cer_18_0_14_0, deoxycer_dihydro_cer_18_0_24_1};

cmaps = [0, 0, 0;...
    0, 0, 1;...
    0, 1, 0;...
    1, 0, 0;...
    0, 1, 1;...
    1, 0, 1;...
    1, 1, 0;...
    0.61,0.4,0.12;...
    1, 0.5, 0.31;...
    0.7, 0.13,0.13;...
    0.69, 0.19, 0.38;...
    1, 0.75, 0.8;...
    0.53, 0.15, 0.34;...
    0.98, 0.5, 0.45;...
    1, 0.27, 0;...
    1, 0.6, 0.07;...
    0.92, 0.56, 0.33;...
    1, 0.89, 0.52;...
    0.85, 0.65, 0.41;...
    1, 0.38, 0;...
    0.96, 0.87, 0.7;...
    0.04, 0.09, 0.27;...
    0.01, 0.66, 0.62;...
    0.5, 1, 0.83;...
    0.5, 0.16, 0.16;...
    0.5, 1, 1;...
    0.18, 0.3, 0.3;...
    0.41, 0.41, 0.41;...
    0.44, 0.50, 0.56;...
    0.83, 0.83, 0.83;...
    0.25, 0.41, 0.88;...
    0.52, 0.80, 0.98;...
    0.68, 0.93, 0.93];

figure('Units', 'inches', 'OuterPosition', [0.25 0.25 3 3])

j=0:0.2:5.4;
for i = 1: numel(reference_dataset)
    reference = reference_dataset{i} + j(i);
    plot(wavenumber_samples, reference, 'lineWidth', 2, 'Color', cmaps(i, :));
    hold on
end
 legend(subtype_name);
 xlabel('Wavenumber (cm^{-1})');
 ylabel('Intensity (au)');
 ax = gca;
 ax.XAxis.LineWidth = 2;
 ax.YAxis.LineWidth = 2;
 set(gca,'fontsize',12,'FontWeight','bold');
 exportgraphics(gca, strcat('figure2', total_reference, '.tiff'), 'Resolution', 2000);