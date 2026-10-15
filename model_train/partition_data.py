import os
import shutil
from PIL import Image
import random
import cv2

# Define class names and directories
class_names = ['White', 'Straight', 'Left', 'Right', 'T', 'T-Left', 'T-Right', 'Cross', 'Ambiguous', 'End']
data_dir = "data2"
output_dir = "/home/zakriya/Downloads/bin_data/data"
yolo_dir = "/home/zakriya/Downloads/bin_data/dataset"
os.makedirs(output_dir, exist_ok=True)

# Create directories for each class
for class_name in class_names:
    os.makedirs(os.path.join(output_dir, class_name), exist_ok=True)

# # Key bindings for classes
# key_bindings = {str(i + 1): class_name for i, class_name in enumerate(class_names)}
# print("Key Bindings:")
# for key, class_name in key_bindings.items():
#     print(f"Press {key} for {class_name}")

# # Classify images
# for image_name in os.listdir(data_dir):
#     image_path = os.path.join(data_dir, image_name)
#     if not os.path.isfile(image_path):
#         continue

#     image = cv2.imread(image_path)
#     cv2.imshow("Classify Image", image)

#     while True:
#         key = cv2.waitKey(0) & 0xFF  # Wait for key press
#         if chr(key) in key_bindings:
#             class_name = key_bindings[chr(key)]
#             save_path = os.path.join(output_dir, class_name, image_name)
#             shutil.copy(image_path, save_path)
#             # print(f"Saved {image_name} to {class_name}")
#             break
#         elif chr(key) == 'q':  # Press 'q' to quit
#             print("Exiting classification.")
#             cv2.destroyAllWindows()
#             exit()

# cv2.destroyAllWindows()

# Split data into train, test, and val sets
def split_data(source_dir, target_dir, train_ratio=0.7, val_ratio=0.2, test_ratio=0.1):
    os.makedirs(target_dir, exist_ok=True)

    for class_name in class_names:
        class_dir = os.path.join(source_dir, class_name)
        images = os.listdir(class_dir)
        random.shuffle(images)

        train_cutoff = int(len(images) * train_ratio)
        val_cutoff = int(len(images) * (train_ratio + val_ratio))

        splits = {
            "train": images[:train_cutoff],
            "val": images[train_cutoff:val_cutoff],
            "test": images[val_cutoff:]
        }

        for split, split_images in splits.items():
            split_dir = os.path.join(target_dir, split, class_name)
            os.makedirs(split_dir, exist_ok=True)
            for img in split_images:
                shutil.copy(os.path.join(class_dir, img), os.path.join(split_dir, img))

# Run the splitting process
split_data(output_dir, yolo_dir)

print("Data has been classified and split into train, test, and val sets.")
