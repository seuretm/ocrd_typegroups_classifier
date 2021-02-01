import torch
from torch.autograd import Variable
from torch.autograd import Function
from torchvision import models
from torchvision import utils
import cv2
import sys
import numpy as np
import argparse
import torch.nn.functional as F
from math import floor
from pprint import pprint
from tqdm import tqdm
import os

from ocrd_typegroups_classifier.typegroups_classifier import TypegroupsClassifier

# This code is highly inspired by https://github.com/jacobgil/pytorch-grad-cam
# The main differences are as follows:
# - The patch-wise approach for larger images,
# - The removal of the guided backpropagation,
# - A refactoring of the code to make it slightly less network-dependent,
# - The common normalization of the heatmpas to allow for a comparison
# Some minor differences are present as well.

class FeatureExtractor():
	""" Class for extracting activations and 
	registering gradients from targetted intermediate layers """
	def __init__(self, fe, target_layers):
		self.fe = fe
		self.gradients = []
		self.target_layers = target_layers

	def save_gradient(self, grad):
		self.gradients.append(grad)

	def __call__(self, x):
		outputs = []
		self.gradients = []
		n = 0
		for mod in self.fe:
			x = mod(x)
			if n in self.target_layers:
				x.register_hook(self.save_gradient)
				outputs += [x]
			n+=1
		if len(outputs)==0:
			print('Invalid target layer - use values between 0 and %d' %(n-1))
			quit()
		return outputs, x

class ModelOutputs():
	""" Class for making a forward pass, and getting:
	1. The network output.
	2. Activations from intermeddiate targetted layers.
	3. Gradients from intermeddiate targetted layers. """
	def __init__(self, fe, cl, model, target_layers):
		self.fe = FeatureExtractor(fe, target_layers)
		self.cl = cl
		self.model = model

	def get_gradients(self):
		return self.fe.gradients

	def __call__(self, x):
		target_activations, output  = self.fe(x)
		#output = self.model.pool(output)
		output = F.adaptive_avg_pool2d(output, (1, 1)).view(output.size(0), -1)
		output = output.view(output.size(0), -1)
		output = self.cl(output)
		return target_activations, output

def preprocess_image(img):
	preprocessed_img = img.copy()[: , :, ::-1]
	preprocessed_img = \
		np.ascontiguousarray(np.transpose(preprocessed_img, (2, 0, 1)))
	preprocessed_img = torch.from_numpy(preprocessed_img)
	preprocessed_img.unsqueeze_(0)
	input = Variable(preprocessed_img, requires_grad = True)
	return input

def show_cam_on_image(img, mask, out, target_size=None):
	heatmap = cv2.applyColorMap(np.uint8(255*mask), cv2.COLORMAP_HOT)
	print('Heatmap:', heatmap.shape)
	heatmap = np.float32(heatmap) / 255
	heatmap = np.transpose(heatmap, (1, 0, 2))
	cam = heatmap + np.float32(img)
	cam = cam / np.max(cam)
	if not target_size is None:
		cam = cv2.resize(cam, target_size)
	cv2.imwrite(out, np.uint8(255 * cam))

class GradCam:
	def __init__(self, fe, cl, model, target_layers, use_cuda):
		self.fe = fe
		self.cl = cl
		self.model = model
		self.fe.eval()
		self.cl.eval()
		self.cuda = use_cuda
		if self.cuda:
			self.fe = fe.cuda()
			self.cl = cl.cuda()
		self.extractor = ModelOutputs(self.fe, self.cl, self.model, target_layers)

	def forward(self, input):
		self.cl(self.fe(input))

	def __call__(self, input, target_dim, index):
		if self.cuda:
			features, output = self.extractor(input.cuda())
		else:
			features, output = self.extractor(input)

		one_hot = np.zeros((1, output.size()[-1]), dtype = np.float32)
		one_hot[0][index] = 1
		one_hot = Variable(torch.from_numpy(one_hot), requires_grad = True)
		if self.cuda:
			one_hot = torch.sum(one_hot.cuda() * output)
		else:
			one_hot = torch.sum(one_hot * output)

		self.fe.zero_grad()
		self.cl.zero_grad()
		one_hot.backward(retain_graph=True)

		grads_val = self.extractor.get_gradients()[-1].cpu().data.numpy()

		target = features[-1]
		target = target.cpu().data.numpy()[0, :]

		weights = np.mean(grads_val, axis = (2, 3))[0, :]
		cam = np.zeros(target.shape[1 : ], dtype = np.float32)

		for i, w in enumerate(weights):
			cam += w * target[i, :, :]
		return cam

class GuidedBackpropReLU(Function):

	def forward(self, input):
		positive_mask = (input > 0).type_as(input)
		output = torch.addcmul(torch.zeros(input.size()).type_as(input), input, positive_mask)
		self.save_for_backward(input, output)
		return output

	def backward(self, grad_output):
		input, output = self.saved_tensors
		grad_input = None

		positive_mask_1 = (input > 0).type_as(grad_output)
		positive_mask_2 = (grad_output > 0).type_as(grad_output)
		grad_input = torch.addcmul(torch.zeros(input.size()).type_as(input), torch.addcmul(torch.zeros(input.size()).type_as(input), grad_output, positive_mask_1), positive_mask_2)

		return grad_input

class GuidedBackpropReLUModel:
	def __init__(self, fe, cl, model, use_cuda):
		self.model = model
		self.model.eval()
		self.fe = fe
		self.cl = cl
		fe.eval()
		cl.eval()
		self.cuda = use_cuda
		if self.cuda:
			self.model = model.cuda()

		# replace ReLU with GuidedBackpropReLU
		for idx, module in fe._modules.items():
			if module.__class__.__name__ == 'ReLU':
				fe._modules[idx] = GuidedBackpropReLU()

	def forward(self, input):
		f = self.model.avgpool(self.fe(input))
		return self.cl(f.view(f.size(0), -1))

	def __call__(self, input, index = None):
		if self.cuda:
			output = self.forward(input.cuda())
		else:
			output = self.forward(input)

		if index == None:
			index = np.argmax(output.cpu().data.numpy())

		one_hot = np.zeros((1, output.size()[-1]), dtype = np.float32)
		one_hot[0][index] = 1
		one_hot = Variable(torch.from_numpy(one_hot), requires_grad = True)
		if self.cuda:
			one_hot = torch.sum(one_hot.cuda() * output)
		else:
			one_hot = torch.sum(one_hot * output)

		#self.fe.zero_grad()
		#self.cl.zero_grad()
		one_hot.backward(retain_graph=True)

		output = input.grad.cpu().data.numpy()
		output = output[0,:,:,:]
		
		return output
def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--layer', type=int, default=11, help='Layer number (0-11)')
    parser.add_argument('--image_path', type=str, help='Input image relative/full path')
    args = parser.parse_args()
    args.use_cuda = torch.cuda.is_available()

    return args

if __name__ == '__main__':
    """ python heatmap.py <path_to_image>
    1. Loads an image with opencv.
    2. Preprocesses it for VGG19 and converts to a pytorch variable.
    3. Makes a forward pass to find the category index with the highest score,
    and computes intermediate activations.
    Makes the visualization. """

    args = get_args()
    
    pth = args.image_path
    fn = pth.split(os.sep)[-1]
    output_name = os.path.splitext(fn)[0]
    # Can work with any model, but it assumes that the model has a 
    # feature method, and a classifier method,
    # as in the VGG models in torchvision.
    
    #grad_cam = GradCam(model = models.vgg19(pretrained=True), target_layer_names = ["35"], use_cuda=args.use_cuda)
    
    # If None, returns the map for the highest scoring category.
    # Otherwise, targets the requested index.
    target_index = 0
    
    nb_classes = 12
    
    result = {}
    for target_index in tqdm(range(nb_classes), desc='Font group'):
        img = cv2.imread(args.image_path, 1)
        img = np.float32(img)
        # Resizing
        h = img.shape[0]
        w = img.shape[1]
        r = 1000 / float(w)
        if w>1000:
            img = cv2.resize(img, (round(w*r), round(h*r)))
        img = img / 255
        
        
        input = preprocess_image(img)
        
        tgc = TypegroupsClassifier.load('ocrd_typegroups_classifier/models/densenet121.tgc')
        
        net = tgc.network
        net_fe = net.feature_extractor()
        net_cl = net.get_classifier()
        grad_cam = GradCam(fe=net_fe, cl=net_cl, model=net, target_layers = [args.layer], use_cuda=args.use_cuda)
        
        #mask = grad_cam(input, (img.shape[0], img.shape[1]), target_index)
        res = None
        hps = 500 # patch size
        vps = 250
        
        # fitting
        hps = int(floor(w / round(w/float(hps))))
        vps = int(floor(h / round(h/float(vps))))
        
        nbh = 0
        for x in range(0, input.shape[3], hps):
            nbh += 1
        nbv = 0
        for y in range(0, input.shape[2], vps):
            nbv += 1
        
        nx = 0
        ny = 0
        if nb_classes==2:
            offset = 1
        else:
            offset = 0
        for x in range(0, input.shape[3], hps):
            row = None
            ny = 0
            for y in range(0, input.shape[2], vps):
                mask = grad_cam(input[:, :, y:(y+vps), x:(x+hps)], (vps, hps), target_index+offset)
                #mask = input[0, 0, y:(y+vps), x:(x+hps)].detach().numpy()
                if nx==0 and ny==2:
                    mask *= 1
                if row is None:
                    row = mask
                else:
                    row = np.concatenate((row, mask), axis=0)
                ny += 1
            if res is None:
                res = row
            else:
                res = np.concatenate((res, row), axis=1)
            nx += 1
        res = np.transpose(res)
        result[target_index] = [res, None]

    # normalizing
    minimum =  float('inf')
    maximum = -float('inf')
    for target_index in range(nb_classes):
        result[target_index][0] = np.maximum(result[target_index][0], 0)
        minimum = np.minimum(minimum, np.min(result[target_index][0]))
        maximum = np.maximum(maximum, np.max(result[target_index][0]))
    
    if not os.path.exists('heatmaps'):
        os.mkdir('heatmaps')
    
    for target_index in range(nb_classes):
        result[target_index][0] = result[target_index][0] - minimum
        result[target_index][0] = result[target_index][0] / (maximum-minimum)
        result[target_index][0] = cv2.resize(result[target_index][0], (img.shape[0], img.shape[1]))
        dst = os.path.join('heatmaps', '%s_%s.jpg' % (output_name, tgc.classMap.id2cl[target_index]))
        print('Storing as %s' % dst)
        show_cam_on_image(img, result[target_index][0], dst, (w,h))
        result[target_index][0] = None
