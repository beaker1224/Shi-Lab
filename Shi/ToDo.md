Thanks to the author of "auto_hyperspectra" for the inspirations from the code.

Now try to setup python code for the LSM 

Inputs:
1. the number of wavelengths
    should have the power follow behind each one, variable check everytime and only change after the power has been changed.
    should have the if average behind, status default to false, check everytime and only change after the average is on
    (should have the channel setting: red / green corresponding to the thing you want to use)

2. when reading the text file, 
    should have "\n-----\n" as the separator for each group setting, "\n" within each group
3. naming system
    the naming should be in the form of "#-wavelength-powermw-zoom#"
4. color recognition and press "LSM Start", color of the scan codition, color of "tunning" and "OK"

5. for now, this little coding project sould only focus on who the get the general setting done. 
    Choosing which channel is not included yet, it should be a feature in the future.