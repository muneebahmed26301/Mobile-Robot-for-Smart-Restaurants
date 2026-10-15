import cv2
import os
import numpy as np

def format_images(input_folder, output_folder):
    # Make sure output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Loop through all files in input folder
    for filename in os.listdir(input_folder):
        file_path = os.path.join(input_folder, filename)
        
        # Only process files that are images
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
            # Read the image
            img = cv2.imread(file_path)
            
            if img is None:
                print(f"Failed to read {file_path}")
                continue
            
            # Format
            thresh_img = cv2.flip(img, 1)
            # img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            # pad = 5
            # img = cv2.copyMakeBorder(img, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=(255, 255))
            # _, thresh_img = cv2.threshold(img, 100, 255, cv2.THRESH_BINARY_INV)
            # kernel = np.ones((5, 5), np.uint8)
            # thresh_img = cv2.morphologyEx(thresh_img, cv2.MORPH_OPEN, kernel, iterations=2)
            # thresh_img = cv2.morphologyEx(thresh_img, cv2.MORPH_CLOSE, kernel)

            # contours, _ = cv2.findContours(thresh_img.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            # if len(contours) > 0:
            #     largest_contour = max(contours, key=cv2.contourArea)
            #     # Create a blank black image
            #     mask = np.zeros_like(thresh_img)
                
            #     # Draw only the largest contour on the mask
            #     cv2.drawContours(mask, [largest_contour], -1, color=255, thickness=cv2.FILLED)
                
            #     # Set final image to mask
            #     thresh_img = mask
            

            # Save to output folder
            output_path = os.path.join(output_folder, f"f{filename}")
            cv2.imwrite(output_path, thresh_img)
            print(f"Saved format image to {output_path}")

# Example usage:
input_folder = '/home/zakriya/Downloads/bin_data/data/T-Left'
output_folder = '/home/zakriya/Downloads/bin_data/data/T-Right'
format_images(input_folder, output_folder)

# for folder in os.listdir(input_folder):
#     format_images(os.path.join(input_folder, folder), os.path.join(output_folder, folder))
