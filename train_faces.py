import cv2
import numpy as np
import os

def train_model():
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    
    face_samples = []
    ids = []
    path = 'static/faces'

    for f in os.listdir(path):
        if not f.endswith(('.jpg', '.png')): continue
        
        # Get ID from filename (e.g., "1.jpg" -> ID 1)
        student_id = int(f.split('.')[0])
        img = cv2.imread(os.path.join(path, f), cv2.IMREAD_GRAYSCALE)
        
        faces = detector.detectMultiScale(img)
        for (x, y, w, h) in faces:
            face_samples.append(img[y:y+h, x:x+w])
            ids.append(student_id)

    recognizer.train(face_samples, np.array(ids))
    recognizer.save('trainer.yml')
    print("✓ Model trained and saved as trainer.yml")

if __name__ == "__main__":
    train_model()