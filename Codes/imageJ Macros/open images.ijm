// Step 1: Define wavelengths to subtract from the background wavelength
subtract_wavelengths = newArray("841nm", "843nm", "845nm"); // Add more wavelengths here as needed
background_wavelength = "862nm";  // Modify this as needed

// Step 2: Prompt the user to select a folder
dir = getDirectory("Choose a Directory, the folder where your images are");

// Step 3: Get the list of files in the selected folder
fileList = getFileList(dir);

// Step 4: Open all .oir images initially using Bio-Formats Importer
for (i = 0; i < fileList.length; i++){
    if (endsWith(fileList[i], ".oir")) {
        run("Bio-Formats Importer", "open=[" + dir + fileList[i] + "] autoscale color_mode=Default view=Hyperstack stack_order=XYCZT");
        print("Opened: " + fileList[i]);
    }
}
