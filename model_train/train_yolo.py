from ultralytics import YOLO

model = YOLO("yolo11n-cls.pt")

results = model.train(data="/home/zakriya/Downloads/dataset1_2", epochs=25, imgsz=192, translate=0.0, scale=0.0, fliplr=0.0, mosaic=0.0, erasing=0)
