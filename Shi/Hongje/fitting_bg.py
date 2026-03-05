import numpy as np
from skimage import io
from scipy.interpolate import interp1d
from scipy.optimize import minimize, Bounds, curve_fit
import pandas as pd
import csv

# Please type the csv file name that will be processed with address
# After processing, the 

Filename = 'G:/Hongje/Shuo/Rapamycin/Raw/Rapa_D10/Gut/1_RAPA/RAPA_D10_RAPA_1'

range_start = 1000
range_end = 3900

data = pd.DataFrame(pd.read_csv(Filename + '.csv')).to_numpy()

axis_x = np.arange(range_start, range_end, 1)

interp_data = interp1d(data[:, 0], data[:, 1])

new_data = np.zeros([axis_x.shape[0], 2])

new_data[:, 0] = axis_x
new_data[:, 1] = interp_data(axis_x)

new_data[:, 1] = new_data[:, 1] - np.min(new_data[:, 1])


def func(parm):
    
    wavenumber = new_data[2220:2800, 0]
    inten = new_data[2220:2800, 1]
                
    fun = parm[0]*np.exp((-np.square(wavenumber-parm[1]))/(2*parm[2]*parm[2])) + parm[3]
            
    return np.mean(np.square(inten - fun))
     
        
        
init_val = [np.max(new_data[:, 1])/2, 3500, 100, np.min(new_data[:, 1])]
        
lower_bounds = [0, 3300, 10, np.min(new_data[:, 1])]

upper_bounds = [np.max(new_data[:, 1]), 3600, 500, np.max(new_data[:, 1])]
        
bounds = Bounds(lower_bounds, upper_bounds)
        
result = minimize(func, init_val, method='Nelder-Mead', tol=1e-20, bounds=bounds)
        
        
res_parm = result.x


bg_curve = np.zeros([data.shape[0],])

bg_curve = res_parm[0]*np.exp((-np.square(new_data[:, 0]-res_parm[1]))/(2*res_parm[2]*res_parm[2])) + res_parm[3]

sub_data = new_data[:, 1] - bg_curve

sub_data = sub_data - np.mean(sub_data[1400:1500])




f = open(Filename + '_spontaneous_Raman_BG_subtracted.csv', 'w', encoding='utf-8', newline='')

writer = csv.writer(f)

writer.writerow(['Wavenumber', 'Intensity', 'BG'])


for i in range(0, axis_x.shape[0]):
    
    writer.writerow([new_data[i, 0], sub_data[i], bg_curve[i]])


f.close()

