// Custom save shortcut, if not work please change ctrl+s to s and press s to save both
macro "Save as TIFF and PNG [ctrl+s]" {
    // Get the current image title
    title = getTitle();
    
    // Set the save directory (modify this to your desired folder)
    saveDir = getDirectory("save to...");

    // Save the current image as TIFF
    saveAs("Tiff", saveDir + title);

    // Save the current image as PNG
    saveAs("PNG", saveDir + title);
}
