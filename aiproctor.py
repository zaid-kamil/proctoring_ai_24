from ultralytics import YOLO
import os
import cv2
# start proctoring on a thread
classes_to_count = [0]
from threading import Thread 
from datetime import datetime, timedelta
from database import User, Exam, Question, Attempt, ProctorLog, opendb, save
from ultralytics.solutions import object_counter
stop_proctoring = False


class Proctor:
    def __init__(self, user_id, exam_id, attempt_id, duration=60*60):
        self.user_id = user_id
        self.exam_id = exam_id
        self.attempt_id = attempt_id
        self.status = 0
        self.count = 0
        self.cwcount = {}
        self.start_time = datetime.now()
        print(f'Starting proctoring for at {self.start_time}')
        self.end_time = self.start_time + timedelta(seconds=duration)
        # load model
        self.model = YOLO("yolov8n-pose.pt")
        # video capture
        self.cap = cv2.VideoCapture(0)
        w, h, fps = (int(self.cap.get(x)) for x in (cv2.CAP_PROP_FRAME_WIDTH, cv2.CAP_PROP_FRAME_HEIGHT, cv2.CAP_PROP_FPS))
        self.region = [(10,10), (w-10, 10), (w-10, h-10), (10, h-10)]
        # video writer  
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.video_save_path = f"static/protoring/exam_{self.user_id}_{self.exam_id}_{self.attempt_id}.mp4"
        self.video_writer = cv2.VideoWriter(
            self.video_save_path,
            fourcc, fps, (w, h)
        )
        # init object counter
        self.counter = object_counter.ObjectCounter()
        self.counter.set_args(
            view_img=True,
            reg_pts=self.region,
            classes_names=self.model.names,
            draw_tracks=True,
            line_thickness=2
        )
        

    def start_proctoring(self):
        print(f'Proctoring started for user {self.user_id} exam {self.exam_id} attempt {self.attempt_id}')
        print(f'Proctoring will end at {self.end_time}')
        frame_count = 0
        self.status = 1
        while self.cap.isOpened():
            success, im = self.cap.read()
            if not success:
                print("Video capture failed")
                break
            if self.status == 2:
                break
            if self.status == 1:
                if datetime.now() > self.end_time:
                    self.status = 2
                    break
            frame_count += 1
            tracks = self.model.track(
                im, 
                classes=classes_to_count,
                verbose=False,
                persist=True,
            )
            im = self.counter.start_counting(im, tracks)
            self.count = self.counter.in_counts
            self.cwcount = self.counter.class_wise_count
            self.video_writer.write(im)
            if frame_count % 10 == 0:
                print(f'Frame {frame_count}')
        print('Proctoring ended')

    def stop_proctoring(self):
        self.video_writer.release()
        self.status = 2
        cv2.destroyAllWindows()
        self.thread.join() # wait for the thread to finish

    def get_status(self):
        return self.status


# start proctoring
if __name__ == '__main__':
    proctor = Proctor(1, 1, 1, 10)