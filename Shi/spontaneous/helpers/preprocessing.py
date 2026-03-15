from __future__ import annotations

from pathlib import Path
from typing import Literal, Union, Optional, Tuple, Dict, List, Any

import numpy as np
import pandas as pd

from scipy.interpolate import interp1d
from scipy.optimize import minimize, Bounds, curve_fit
import matplotlib.pyplot as plt


# Please type the csv file name that will be processed with address
# After processing, the 
def fitted_bg_subtraction(wn: np.ndarray, intensity: np.ndarray, range_start: int = 1000, range_end: int = 3900) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    '''
    This function performs background subtraction on a Raman spectrum by fitting a Gaussian curve to the background and subtracting it from the original spectrum.
    Parameters:
    wn (np.ndarray): The wavenumber axis data.
    intensity (np.ndarray): The intensity data corresponding to the wavenumber axis.
    range_start (int): The starting point of the range to consider for background fitting. default is 1000.
    range_end (int): The ending point of the range to consider for background fitting. default is 3900.
    Returns:
    Tuple[np.ndarray, np.ndarray, np.ndarray]: A tuple containing the wavenumber axis, 
    the background-subtracted intensity, and the fitted background curve.
    '''

    # Combine into 2D array for interpolation
    data = np.column_stack((wn, intensity))

    try:
        interp_data = interp1d(data[:, 0], data[:, 1])
    except ValueError as e:
        print(f"Error occurred while interpolating data: {e}, possible due to range too large to include all data points.")
        return np.array([]), np.array([]), np.array([])

    axis_x = np.arange(range_start, range_end, 1)
    new_data = np.zeros([axis_x.shape[0], 2])

    new_data[:, 0] = axis_x # from range start to end with step of 1
    new_data[:, 1] = interp_data(axis_x) # interpolate the intensity values at the new wavenumber axis

    new_data[:, 1] = new_data[:, 1] - np.min(new_data[:, 1]) # shift the intensity values so that the minimum is at zero


    def func(parm): # define the objective function to minimize, which is the mean squared error between the actual intensity and the fitted Gaussian curve
        # modification here:
        # wavenumber = new_data[2220:2800, 0]
        # inten = new_data[2220:2800, 1]
        # but the above was built on the assumption that the input data has a wavenumber range from 1000 to 3900, which may not always be the case.
        # To make it more flexible, we can use the range_start and range_end parameters to determine the indices for the fitting range based on the new_data's wavenumber axis.
        start = 3220-range_start
        try:
            wavenumber = new_data[start:start+580, 0]
            inten = new_data[start:start+580, 1]
        except IndexError as e:
            print(f"Error occurred while slicing data for fitting: {e}, possible don't have data greater than 3800 cm-1.")
            return np.inf # return infinity to indicate that the fitting cannot be performed due to insufficient data points in the specified range
                    
        fun = parm[0]*np.exp((-np.square(wavenumber-parm[1]))/(2*parm[2]*parm[2])) + parm[3]
                
        return np.mean(np.square(inten - fun))
        
            
    # those values are index independent, 
    # so they should be the same regardless of the input data's wavenumber range, 
    # as long as it includes the fitting range.
    init_val = [np.max(new_data[:, 1])/2, 3500, 100, np.min(new_data[:, 1])]
            
    lower_bounds = [0, 3300, 10, np.min(new_data[:, 1])]

    upper_bounds = [np.max(new_data[:, 1]), 3600, 500, np.max(new_data[:, 1])]
            
    bounds = Bounds(lower_bounds, upper_bounds)
            
    result = minimize(func, init_val, method='Nelder-Mead', tol=1e-20, bounds=bounds)
            
            
    res_parm = result.x


    bg_curve = np.zeros([data.shape[0],])

    bg_curve = res_parm[0]*np.exp((-np.square(new_data[:, 0]-res_parm[1]))/(2*res_parm[2]*res_parm[2])) + res_parm[3]

    sub_data = new_data[:, 1] - bg_curve

    baseline_mask = (new_data[:, 0] >= 2400) & (new_data[:, 0] <= 2500)
    sub_data = sub_data - np.mean(sub_data[baseline_mask])

    return new_data[:, 0], sub_data, bg_curve

def spectra_bg_subtraction(wn: np.ndarray, intensity: np.ndarray, bg_wn: np.ndarray, bg_intensity: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    '''
    This function performs background subtraction on a Raman spectrum by intaking the raw wavenumber and intensity data, 
    and subtracting it from the background spectrum.  The background is first interpolated to the
    sample wavenumber axis.  Returns the wavenumber axis and the background-subtracted intensity.

    Note
    ----
    The OH region of the spectrum can become strongly negative after subtraction –
    handle this with `simple_baseline_correction` or another baseline routine if needed.

    Parameters:
    -----------
    wn (np.ndarray): The wavenumber axis data for the sample.
    intensity (np.ndarray): The intensity data corresponding to the sample wavenumber axis.
    bg_wn (np.ndarray): The wavenumber axis data for the background spectrum.
    bg_intensity (np.ndarray): The intensity data for the background spectrum.

    Returns:
    --------
    Tuple[np.ndarray, np.ndarray]: A tuple containing the sample wavenumber axis and the
        background-subtracted intensity.
    '''
    # make sure inputs are numpy arrays
    wn = np.asarray(wn)
    intensity = np.asarray(intensity)
    bg_wn = np.asarray(bg_wn)
    bg_intensity = np.asarray(bg_intensity)

    # interpolate background onto sample wavenumber grid
    interp_bg = interp1d(bg_wn, bg_intensity, bounds_error=False, fill_value='extrapolate')
    bg_on_sample = interp_bg(wn)

    # subtract and return
    subtracted = intensity - bg_on_sample
    return wn, subtracted

def simple_baseline_correction(wn: np.ndarray, intensity: np.ndarray, cell_silent_start: int = 2300, cell_silent_end: int = 2600, trim = None, min_max: bool = True) -> Tuple[np.ndarray, np.ndarray]:
    '''
    This function performs simple baseline correction on a Raman spectrum by setting
    the average of the intensity values from the cell silent region as zero line.
    Every point below this zero line will be forcibly shifted up to be zero. 
    Default cell silent region is between 2300 and 2600 cm-1.
    Parameters:
    wn (np.ndarray): The wavenumber axis data.
    intensity (np.ndarray): The intensity data corresponding to the wavenumber axis.
    cell_silent_start (int): The starting point of the cell silent region. default is 2300.
    cell_silent_end (int): The ending point of the cell silent region. default is 2600.
    trim (optional, int): A int that decide if you would like to trim the spectrum with wavenumber above this value. default is None.
    min_max (bool): Whether to perform min-max normalization. default is True.
    Returns:
    Tuple[np.ndarray, np.ndarray]: A tuple containing the wavenumber axis and the baseline-corrected intensity.
    '''
    cell_silent_mask = (wn >= cell_silent_start) & (wn <= cell_silent_end)
    baseline = np.mean(intensity[cell_silent_mask])
    corrected_intensity = intensity.copy()
    corrected_intensity[corrected_intensity < 0] = 0
    if min_max:
        corrected_intensity = (corrected_intensity - np.min(corrected_intensity)) / (np.max(corrected_intensity) - np.min(corrected_intensity))
    if trim is not None:
        trim_mask = wn <= trim
        wn = wn[trim_mask]
        corrected_intensity = corrected_intensity[trim_mask]
    return wn, corrected_intensity

def polynomial_baseline_correction(wn: np.ndarray, intensity: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    '''
    This function performs baseline correction on a Raman spectrum by fitting a polynomial to the baseline and subtracting it from the original spectrum.
    Parameters:
    wn (np.ndarray): The wavenumber axis data.
    intensity (np.ndarray): The intensity data corresponding to the wavenumber axis.
    Returns:
    Tuple[np.ndarray, np.ndarray]: A tuple containing the wavenumber axis and the baseline-corrected intensity.
    '''
    # Fit a polynomial to the baseline
    coeffs = np.polyfit(wn, intensity, deg=3)
    baseline = np.polyval(coeffs, wn)

    # Subtract the baseline from the original intensity
    corrected_intensity = intensity - baseline

    return wn, corrected_intensity