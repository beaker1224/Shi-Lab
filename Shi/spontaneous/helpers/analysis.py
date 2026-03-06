'''
This module contains statstical tests functions, along with ratio calculators

 important: according to the paper, analysis must be done on the raw spectra, before normalizeation or baseline correction
 but this doesn't mean we can't do background subtraction first, 
 since that is a separate step from baseline correction and normalization.
'''
import numpy as np
from typing import Tuple
from scipy.stats import ttest_ind

def peak_ratio_calculator(wn: np.ndarray, intensity: np.ndarray, peak1: float, peak2: float) -> float:
    '''
    This function calculates the ratio of two peaks in a Raman spectrum.
    Parameters:
    wn (np.ndarray): The wavenumber axis data.
    intensity (np.ndarray): The intensity data corresponding to the wavenumber axis.
    peak1 (float): The wavenumber of the first peak.
    peak2 (float): The wavenumber of the second peak.
    Returns:
    float: The ratio of the two peaks.
    '''
    # Find the indices of the peaks
    idx1 = np.argmin(np.abs(wn - peak1))
    idx2 = np.argmin(np.abs(wn - peak2))
    # Calculate the ratio of the two peaks
    ratio = intensity[idx1] / intensity[idx2] if intensity[idx2] != 0 else np.nan
    return ratio

def area_under_curve_calculator(wn: np.ndarray, intensity: np.ndarray, peak_range1: tuple[float, float], peak_range2: tuple[float, float]):
    '''
    This function calculates the area under the curve for a specified range in a Raman spectrum.
    Parameters:
    wn (np.ndarray): The wavenumber axis data.
    intensity (np.ndarray): The intensity data corresponding to the wavenumber axis.
    peak_range1 (tuple[float, float]): The start and end points of the first peak's range.
    peak_range2 (tuple[float, float]): The start and end points of the second peak's range.
    Returns:
    float: The area under the curve for the specified range.
    '''
    # Find indices within the specified range
    mask1 = (wn >= peak_range1[0]) & (wn <= peak_range1[1])
    mask2 = (wn >= peak_range2[0]) & (wn <= peak_range2[1])
    wn_range1 = wn[mask1]
    intensity_range1 = intensity[mask1]
    wn_range2 = wn[mask2]
    intensity_range2 = intensity[mask2]

    # Calculate the area under the curve using numerical integration
    area1 = np.trapezoid(intensity_range1, wn_range1)
    area2 = np.trapezoid(intensity_range2, wn_range2)
    return area1, area2

def t_test_calculator(group1: np.ndarray, group2: np.ndarray) -> Tuple[float, float]:
    '''
    This function performs a t-test between two groups of data.
    Parameters:
    group1 (np.ndarray): The data for the first group.
    group2 (np.ndarray): The data for the second group.
    Returns:
    Tuple[float, float]: The t-statistic and p-value from the t-test.
    '''
    t_statistic, p_value = ttest_ind(group1, group2, equal_var=False)
    return t_statistic, p_value