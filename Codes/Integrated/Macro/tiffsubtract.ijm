// File: Apply_LUTs_Only.ijm
// Description: This macro opens pre-processed TIFF images from a user-selected folder
// and applies a specific Look-Up Table (LUT) to each one based on its filename.
// The images are left open for manual contrast adjustment.

// --- Step 1: Get User Input ---
// Ask the user to select the folder containing the masked .tif files.
dir = getDirectory("Choose the folder with your masked ROI .tif files");
if (dir == "") exit("User cancelled the dialog"); // Exit if the user cancels the selection.

// --- Step 2: Initial Setup ---
// Get a list of all files within the chosen directory.
list = getFileList(dir);

// Turn on batch mode. This makes the macro run faster in the background and
// prevents intermediate image windows from flickering on the screen.
setBatchMode(true);

// --- Step 3: Define Processing Rules for Different Image Types ---
// Define the unique identifiers for wavelength images and their corresponding LUTs.
wavelength_identifiers = newArray("787.6nm", "791.3nm", "794.6nm", "797.2nm", "841.8nm", "844.6nm");
wavelength_luts = newArray("Yellow", "Red", "Cyan", "Green", "Magenta", "Cyan Hot");

// Define the unique identifiers for the other images, which all share the same LUT.
other_identifiers = newArray("CD_CH-lipid", "CD_CH-protein", "uns_sat");
other_lut = "Royal";

// --- Step 4: Main Processing Loop ---
// This loop iterates through every file in the directory.
for (i = 0; i < list.length; i++) {
currentFile = list[i];
wasProcessed = false; // A flag to check if a file has been handled.

// Part A: Check if the current file is a wavelength image.
for (j = 0; j < wavelength_identifiers.length; j++) {
    if (indexOf(currentFile, wavelength_identifiers[j]) > -1) {
        // If it's a match, open the file.
        open(dir + currentFile);
        
        // Apply the correct LUT based on the identifier.
        run(wavelength_luts[j]);
        
        wasProcessed = true; // Mark the file as processed.
        break; // Exit this inner loop and move to the next file.
    }
}

// If the file was processed above, the 'continue' command skips the next check.
if (wasProcessed) {
    continue;
}

// Part B: Check if the current file is one of the other specified types.
for (j = 0; j < other_identifiers.length; j++) {
    if (indexOf(currentFile, other_identifiers[j]) > -1) {
        // If it's a match, open it.
        open(dir + currentFile);
        
        // Apply the "Royal" LUT.
        run(other_lut);
        
        break; // Exit this inner loop and move to the next file.
    }
}

}

// --- Step 5: Final Display ---
// Turn off batch mode to display all the final, processed image windows.
setBatchMode("exit and display");

// Arrange the resulting windows neatly for easy viewing.
run("Tile");

// Print a confirmation message to the Log window.
print("Macro finished successfully. Images are open for contrast adjustment.");