
import datetime
import time

import imutils
from imutils.video import VideoStream
from keras.models import model_from_json

from car import Car
import matplotlib.image as mpimg
import numpy as np
import pandas as pd
import cv2


class Driver:
    
    def __init__(self, start_camera=True):

        # load json and create model
        json_file = open('model.json', 'r')
        loaded_model_json = json_file.read()
        json_file.close()
        self.model = model_from_json(loaded_model_json)
        
        # load weights into new model
        self.model.load_weights("model.h5")
        print("Loaded model from disk")
        
        # Load class descriptions
        self.signnames = pd.read_csv("signnames.csv")
        
        # start engine
        self.car = Car()
        
        # start camera
        if start_camera == True:
            self.camera()
        
    def turn_car(self, predicted_sign):
        
        if predicted_sign == "Stop":
            self.car.stop()
        elif predicted_sign == "Turn left ahead":
            self.car.left()
        elif predicted_sign == "Turn right ahead":
            self.car.right()
        else:
            self.car.forward()
            
    def camera(self):
        vs = VideoStream(usePiCamera=False).start()
        time.sleep(2.0)
        
        while True:
            # grab the frame from the threaded video stream 
            try:
                oframe = vs.read()
            except:
                continue
            
            roi, annotated_frame, lt = self.pre_process(oframe)
            roi_orig = roi
            try:
                roi = cv2.resize(roi, (32, 32)) 
            except:
                continue
            
            predicted_sign, confidence = self.predict(roi)
            msg = "{} {}%".format(predicted_sign, confidence)
            
            # make car move
            self.turn_car(predicted_sign)
            
            # show the frame
            annotated_frame = cv2.cvtColor(annotated_frame, cv2.COLOR_RGB2BGR)
            cv2.putText(annotated_frame, msg, (lt[0]+50, lt[1]+10), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            cv2.imshow("Frame", annotated_frame)
            key = cv2.waitKey(1) & 0xFF
            
            # if the `q` key was pressed, break from the loop
            if key == ord("q"):
                cv2.imwrite("images/roi_orig.jpg", roi_orig)
                print("saved")
                break
            
        # do a bit of cleanup
        cv2.destroyAllWindows()
        vs.stop()
        
    def test_predict(self, img):
        #img, annotated_frame = self.pre_process(img)
        img = cv2.resize(img, (32, 32)) 
        predicted_sign, confidence = self.predict(img)
        print("Testing: {} {}".format(predicted_sign, confidence))
        
    def predict(self, img):
        # convert to numpy array, expected input type of the model
        input = np.asarray([img])

        # make predictions from the previously trained model
        preds = self.model.predict(input)
        idx = np.argmax(preds, axis=1)[0]
        predicted_sign = self.signnames['SignName'][idx]
        confidence = 100 * preds[0][idx]

        return predicted_sign, confidence

    def pre_process(self, image):
        
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        clone = image.copy()
        copy = image.copy()
        
        # apply canny edge detect
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        auto = imutils.auto_canny(blurred)

        # find all contours in the image and draw ALL contours on the image
        (_, cnts, _) = cv2.findContours(auto, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # loop over the contours 
        roi_cnt = None
        max_area_cnt = 0
        for (i, c) in enumerate(cnts):
            # compute the area of the contour
            area = cv2.contourArea(c)
            if area > max_area_cnt:
                max_area_cnt = area
                roi_cnt = c
                
        # draw bounding box
        box = cv2.minAreaRect(roi_cnt)
        box = np.int0(cv2.boxPoints(box))

        lb = box[0]
        lt = box[1]
        rt = box[2]
        rb = box[3]
        
        roi = clone[lt[1]:lb[1], lt[0]:rb[0]]
        cv2.drawContours(copy, [box], -1, (0, 0, 255), 2)
        return roi, copy, lt
        
if __name__ == '__main__':
    
    image = cv2.imread('images/turn_right.jpg')
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    Driver(start_camera=False).test_predict(image)
    
    print("Done")