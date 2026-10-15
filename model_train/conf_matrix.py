import os
from ultralytics import YOLO
import numpy as np
from sklearn.metrics import confusion_matrix, classification_report
import seaborn as sns
import matplotlib.pyplot as plt

# Define class names
class_names = ['White', 'Straight', 'Left', 'Right', 'T', 'T-Left', 'T-Right', 'Cross', 'Ambiguous', 'End']

# Load YOLO model
model = YOLO("./bin_real.pt")

# Paths
dataset_path = "/home/zakriya/Downloads/bin_data/data"  # Update with the root folder containing class subfolders

# Initialize ground truth and predictions
y_true = []
y_pred = []

# Iterate through each class folder
for class_name in class_names:
    class_folder = os.path.join(dataset_path, class_name)
    if not os.path.isdir(class_folder):
        continue

    # Process each image in the folder
    for img_name in os.listdir(class_folder):
        img_path = os.path.join(class_folder, img_name)
        if not img_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue

        # Perform prediction
        results = model.predict(img_path, imgsz=192)
        pred_idx = results[0].probs.top1  # Index of the predicted class
        pred_class = results[0].names[pred_idx]  # Name of the predicted class

        # Append ground truth and predicted class
        y_true.append(class_name)
        y_pred.append(pred_class)

# Generate confusion matrix
cm = confusion_matrix(y_true, y_pred, labels=class_names)

# Plot confusion matrix
plt.figure(figsize=(12, 8))
sns.heatmap(cm, annot=True, fmt='d', cmap="Blues", xticklabels=class_names, yticklabels=class_names)
plt.xlabel('Predicted Class')
plt.ylabel('True Class')
plt.title('Confusion Matrix')
plt.savefig("confusion_matrix.png", dpi=300)
plt.show()

# Print classification report
print("\nClassification Report:")
print(classification_report(y_true, y_pred, target_names=class_names))
