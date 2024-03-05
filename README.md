# Visual Recognition System
This project is the Visual Recognition System for the Digital Ocean Laboratory.


 This is the CPU edition, no CUDA or GPU required.

 Based repository: https://github.com/Javacr/PyQt5-YOLOv5

 Models used:

 - Detection ： yolov5
 - Tracking ： PromptVT https://github.com/faicaiwawa/PromptVT


## Usage
### Installation
Create and activate a conda environment:
```
conda create -n VRS python=3.8
conda activate VRS
```
Install the required packages:
```
pip install -r requirements.txt
```

### Quick Start
```
python main.py
```

## Functions

for detection:
1. support image/video/webcam/rstp as input
2. change model
3. change IoU
4. change confidence
5. set latency
6. play/pause/stop
7. result statistics
8. save  detected image/video automatically

for tracking:
1. support image/video/webcam/rstp as input
2.  change model
3. change confidence
4. change search area factor
5. play/pause/stop
6. result statistics
7. save  tracker image/video automatically
8. reset the template during tracking


## To Do List

for detection:
Not yet.

for tracking
1. find a proper way to select the ROI in Qlabel, not in the CV2 popup. 
2. add gpu edition




