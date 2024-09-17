// Step 1: Define wavelengths to subtract from the background wavelength
subtract_wavelengths = newArray("841.0nm", "843.0nm", "845.0nm"); // Add more wavelengths here as needed
background_wavelength = "862.0nm";  // Modify this as needed

// Step 2: Prompt the user to select a folder
dir = getDirectory("Choose a Directory, the folder where your images are");

// Step 3: Get the list of files in the selected folder
fileList = getFileList(dir);


// Arrays to store matched images and subtracted ones
roi_background_images = newArray();
roi_other_images = newArray();
other_wavelengths = newArray();
subtracted_images = newArray();  // Track images involved in subtraction

// Step 5: Sort images by wavelength (background and other wavelengths)
for (i = 0; i < fileList.length; i++) {
    filename = fileList[i];

    // Split the image name using "-"
    split_name = split(filename, "-");
    if(split_name[1].length > 7) {
        continue;
    }
    // Extract ROI number and wavelength
    roi = split_name[0];   // ROI number (first part)
    wavelength = split_name[1];   // Wavelength (second part)
    // print(roi, wavelength);

// YKW, arrays.contains does not work, and idk why
    for (j = 0; j < subtract_wavelengths.length; j++) {
        if (subtract_wavelengths[j] == wavelength) {
            roi_other_images = Array.concat(roi_other_images, filename);
            other_wavelengths = Array.concat(other_wavelengths, wavelength);  // Track for naming results
        }
    }
    if (wavelength == background_wavelength) {
        roi_background_images = Array.concat(roi_background_images, filename);
    } 
}
// ------------------------------------------------
// Function to convert array to a string
function arrayToString(array) {
    str = "";
    for (i = 0; i < array.length; i++) {
        str += array[i];
        if (i < array.length - 1) {
            str += ", "; // Add comma separator
        }
    }
    return str;
}

// Convert arrays to strings for printing
roi_background_images_str = arrayToString(roi_background_images);

// Print the arrays
print("Background images: " + roi_background_images_str);
print("Subtracting images: ");

// -----------------------------------------------------


// Step 6: Perform subtraction for corresponding ROIs and wavelengths
for (i = 0; i < roi_other_images.length; i++) {
    roi_other_name = roi_other_images[i];
    print(roi_other_name);
    split_name = split(roi_other_name, "-");  // Extract ROI number
    roi = split_name[0];
    // Find the corresponding background wavelength image with the same ROI
    for (j = 0; j < roi_background_images.length; j++) {
        roi_background_name = roi_background_images[j];
        
        // Match by ROI (first part of the name)
        if (startsWith(roi_background_name, roi)) {
            // Open both images for subtraction
            // open(dir + roi_other_name);
            // open(dir + roi_background_name);
            run("Bio-Formats Importer", "open=[" + dir + roi_other_name + "] autoscale color_mode=Default view=Hyperstack stack_order=XYCZT");
            run("Bio-Formats Importer", "open=[" + dir + roi_background_name + "] autoscale color_mode=Default view=Hyperstack stack_order=XYCZT");


            // Subtract background image from other wavelength image
            run("Image Calculator...", "operation=Subtract image1=[" + roi_other_name + "] image2=[" + roi_background_name + "] create");

            // Track subtracted images to avoid reopening
            subtracted_images = Array.concat(subtracted_images, roi_other_name);

            // Close the original images
            close(roi_other_name);
            close(roi_background_name);
        }

    }

}
subtracted_images = Array.concat(subtracted_images, roi_background_images);

print("subtracted_images:" + arrayToString(subtracted_images));

// Step 7: Open all images that were not involved in subtraction
for (i = 0; i < fileList.length; i++) {
    filename = fileList[i];

    // Check if the image was involved in subtraction
    for (j = 0; j < subtracted_images.length; j++) {
        if ((filename == subtracted_images[j])) {
            j = subtracted_images.length;
        }

        if(j == (subtracted_images.length - 1)) {
            run("Bio-Formats Importer", "open=[" + dir + filename + "] autoscale color_mode=Default view=Hyperstack stack_order=XYCZT");

        }
    }
}
