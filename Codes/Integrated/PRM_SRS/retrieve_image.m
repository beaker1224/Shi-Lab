function single_frame_image = retrieve_image(images)
images = squeeze(images);
single_frame_image = (images - min(images(:)))/(max(images(:)) - min(images(:)));
end