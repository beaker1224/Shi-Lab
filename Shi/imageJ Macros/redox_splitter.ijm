macro "redox_splitter" {
	// SplitRedoxChannels_SameFolder.ijm
	// Pick one folder; all "*redox*.oir" files there will be split
	// and the TIFFs written back into the same folder.
	
	dir = getDirectory("Choose folder containing your .oir files");
	list = getFileList(dir);
	
	for (i = 0; i < list.length; i++) {
	    name    = list[i];
	    nameLow = toLowerCase(name);
	    if (endsWith(nameLow, ".oir") && indexOf(nameLow, "redox") >= 0) {
	        path = dir + name;
	        
        	run("Bio-Formats Importer", 
            "open=[" + path + "] autoscale color_mode=Default view=Hyperstack " +
            "stack_order=XYCZT");
            
	        title = getTitle();
	
	        // split into C1-title and C2-title
	        run("Split Channels");
	
	        // save channel 1 as basename_fad.tif
	        selectWindow("C1-" + title);
	        saveAs("Tiff", dir
	            + substring(name, 0, 1)
	            + "_fad.tif");
	
	        // save channel 2 as basename_nadh.tif
	        selectWindow("C2-" + title);
	        saveAs("Tiff", dir
	            + substring(name, 0, 1)
	            + "_nadh.tif");
	
	        run("Close All");
    }
}

}