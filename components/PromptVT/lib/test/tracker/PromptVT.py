from ...test.tracker.basetracker import BaseTracker
import torch
from ...train.data.processing_utils import sample_target
import cv2
import os
from ...utils.box_ops import clip_box
#for onnxruntime
from ...test.tracker.utils import PreprocessorX_onnx
import onnxruntime
import multiprocessing
import numpy as np
import time

class PromptVT_onnx(BaseTracker):
    def __init__(self, params, dataset_name,z_path,x_path,dtp_path):
        super(PromptVT_onnx, self).__init__(params)
        providers = ['CPUExecutionProvider']
        self.ort_sess_z = onnxruntime.InferenceSession(z_path, providers=providers)
        self.ort_sess_x = onnxruntime.InferenceSession(x_path, providers=providers)
        self.ort_sess_DTP = onnxruntime.InferenceSession(dtp_path, providers=providers)
        self.preprocessor = PreprocessorX_onnx()
        #print("Testing Dataset: ", dataset_name)
        self.state = None
        # for debug
        self.debug = False
        self.frame_id = 0
        if self.debug:
            self.save_dir = "debug"
            if not os.path.exists(self.save_dir):
                os.makedirs(self.save_dir)
        self.ort_outs_z_1 = []
        self.ort_outs_z_2 = []
        self.ort_z_dict_list = []
        self.Datasetname = dataset_name
        self.conf = 0
        self.interval = 0
        self.z_dict_list = []
        self.fuse_src_temp_8 = None
        self.fuse_src_temp_16 = None
        self.flag = False
        self.update_intervals=[0]
        self.update_intervals[0]=100
        self.model_time_2 = 0
        self.model_time_1 = 0

    def initialize(self, image, info: dict):

        z_patch_arr, _, z_amask_arr = sample_target(image, info['init_bbox'], 2,
                                                    output_sz=128)
        x_patch_arr_s, _, x_amask_arr_s = sample_target(image, info['init_bbox'], 2,
                                                        output_sz=128)
        template1, template_mask1 = self.preprocessor.process(z_patch_arr, z_amask_arr)
        template2, template_mask2 = self.preprocessor.process(x_patch_arr_s, x_amask_arr_s)
        
        ort_inputs_1 = {'img_z': template1, 'mask_z': template_mask1}
        ort_inputs_2 = {'img_z': template2, 'mask_z': template_mask2}
        self.ort_outs_z_1 = self.ort_sess_z.run(None, ort_inputs_1)
        self.ort_outs_z_2 = self.ort_sess_z.run(None, ort_inputs_2)
        self.ort_z_dict_list.append(self.ort_outs_z_1)
        self.ort_z_dict_list.append(self.ort_outs_z_2)
        self.state = info['init_bbox']
        self.frame_id = 0
        self.conf = 0.5
        self.interval = 20


    def track(self, image, info: dict = None,intervals =None,search_factor = None,conf = None):
        H, W, _ = image.shape
        self.frame_id += 1
        x_patch_arr, resize_factor, x_amask_arr = sample_target(image, self.state, search_factor,
                                                                output_sz=320)  # (x1, y1, w, h)
        search, search_mask = self.preprocessor.process(x_patch_arr, x_amask_arr)

        model_time_start = time.time()
        if(self.flag == True or self.frame_id == 1 ):
            ort_inputs_fuse = {'src_temp_8':self.ort_z_dict_list[0][0],
            'src_temp_16' :self.ort_z_dict_list[0][2],
            'dy_src_temp_8':self.ort_z_dict_list[1][0],
            'dy_src_temp_16':self.ort_z_dict_list[1][2]}
            
            fused_temp_8 , fused_temp_16 = self.ort_sess_DTP.run(None, ort_inputs_fuse)
            self.fuse_src_temp_8 = fused_temp_8
            self.fuse_src_temp_16 = fused_temp_16
        self.flag = False

        ort_inputs = {  #self.ort_outs_z_1: [0]src_temp_8 , [2]src_temp_16 , [3]pos_tem8,[4]pos_tem16
                      'img_x':search,
                      'src_temp_8':self.fuse_src_temp_8,
                      'pos_temp_8':self.ort_outs_z_1[3],
                      'src_temp_16':self.fuse_src_temp_16,
                       'pos_temp_16':self.ort_outs_z_1[4]
                      }

        pred_logits , outputs_coord = self.ort_sess_x.run(None, ort_inputs)

        self.model_time_1 = time.time()-model_time_start
        pred_box = (outputs_coord.reshape(4) * 320 / resize_factor).tolist()  # (cx, cy, w, h) [0,1]

        self.state = clip_box(self.map_box_back(pred_box, resize_factor), H, W, margin=10)
        
        conf_score = _sigmoid(pred_logits[0][0]).item()

        for idx, update_i in enumerate(self.update_intervals):
            if self.frame_id % intervals == 0 and conf_score > conf:
                z_patch_arr, _, z_amask_arr = sample_target(image, self.state, 2,
                                                            output_sz=128)  # (x1, y1, w, h)
                template_t,template_mask = self.preprocessor.process(z_patch_arr, z_amask_arr)
                ort_inputs = {'img_z': template_t, 'mask_z': template_mask}
                with torch.no_grad():
                    model_time_start = time.time()
                    ort_outs_z = self.ort_sess_z.run(None, ort_inputs)
                    self.model_time_2 = time.time()-model_time_start
                self.ort_z_dict_list[idx+1] = ort_outs_z  # the 1st element of z_dict_list is template from the 1st frame
                self.flag = True
                
        if(self.flag == True):
            model_time = self.model_time_2 + self.model_time_1
        else:
            model_time = self.model_time_1
        return {"target_bbox": self.state,
                "model_time": model_time,
                "conf": conf_score}

    def map_box_back(self, pred_box: list, resize_factor: float):
        cx_prev, cy_prev = self.state[0] + 0.5 * self.state[2], self.state[1] + 0.5 * self.state[3]
        cx, cy, w, h = pred_box
        half_side = 0.5 * 320 / resize_factor
        cx_real = cx + (cx_prev - half_side)
        cy_real = cy + (cy_prev - half_side)
        return [cx_real - 0.5 * w, cy_real - 0.5 * h, w, h]

def _sigmoid(x):
    return 1 / (1 + np.exp(-x))
