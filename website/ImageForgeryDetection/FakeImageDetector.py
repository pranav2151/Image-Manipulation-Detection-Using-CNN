import os
import ctypes
from keras.models import load_model
import numpy as np
from PIL import Image, ImageChops, ImageEnhance, ImageFilter
import PIL.ImageQt
import cv2 as cv
from matplotlib import pyplot as plt
from website.ImageForgeryDetection.NeuralNets import initClassifier, initSegmenter
from skimage import feature


# Color-image denoising
from skimage.restoration import (denoise_wavelet,estimate_sigma)
from skimage.util import random_noise
# from sklearn.metrics import peak_signal_noise_ratio
import skimage.io

resaved_filename = os.getcwd()+'/media/tempresaved.jpg'


class FID: 
   
   def prepare_image(self,fname):
    image_size = (128, 128)
    print('-----------fname--------------',fname)
    return  np.array(self.convert_to_ela_image(fname,90).resize(image_size)).flatten() / 255.0   #return ela_image as a numpy array

                 
   def predict_result(self,fname):     
      
     
      #model = load_model('C://Users//User//ML//Video_Forgery_Detection//ResNet50_Model//forgery_model_me.hdf5')  #load the trained model 
      model = load_model('C://Users//prana//django_projects//models//ela_casia.h5')  #load the trained model 
      class_names = ['Forged', 'Authentic']  #classification outputs
      test_image = self.prepare_image(fname)
      test_image = test_image.reshape(-1, 128, 128, 3)
      y_pred = model.predict(test_image)
      print('y_pred====',y_pred)
      y_pred_class = int(round(y_pred[0][0]))
      
      prediction= class_names[y_pred_class]
      if y_pred <= 0.5:
         confidence = f'{(1-(y_pred[0][0])) * 100:0.2f}'
      else:
         confidence = f'{(y_pred[0][0]) * 100:0.2f}'
      return (prediction, confidence)
 

   def genMask(self,file_path):
      segmenter=initSegmenter()
      segmenter.load_weights('C://Users//prana//django_projects//models//segmenter_weights.h5')
      print('-----------file-path--------------',file_path)
      testimg=self.convert_to_ela_image(file_path,90).resize((256,256))
      testimg=testimg.getchannel('B')
      test=np.array(testimg)/np.max(testimg)
      test=test.reshape(-1,256,256,1)
      mask=segmenter.predict(test)
      mask=mask.reshape(256,256)
      mask=(mask*255).astype('uint8')
      # plt.figure('Binary Mask')
      # plt.imshow(mask, cmap='gray')
      # plt.show()
      mask_im = Image.fromarray(mask)
      mask_im.save(resaved_filename, 'JPEG')
      return mask_im


   def convert_to_ela_image(self,path,quality):

      print('-----------path--------------',path)
      original_image = Image.open(path).convert('RGB')

      #resaving input image at the desired quality
      resaved_file_name = resaved_filename  
      original_image.save(resaved_file_name,'JPEG',quality=quality)
      resaved_image = Image.open(resaved_file_name)

      #pixel difference between original and resaved image
      ela_image = ImageChops.difference(original_image,resaved_image)
      
      #scaling factors are calculated from pixel extremas
      extrema = ela_image.getextrema()
      max_difference = max([pix[1] for pix in extrema])
      if max_difference ==0:
         max_difference = 1
      scale = 255.0 / max_difference
      
      #enhancing elaimage to brighten the pixels
      ela_image = ImageEnhance.Brightness(ela_image).enhance(scale)
      #ela_image.save("ela_image.png")
      return ela_image


      
   def show_ela(self, file_path,sl=50):
      
      intensity=sl
      ela_im=self.convert_to_ela_image(file_path, 90)
      # plt.figure('Error Level analysis')
      # plt.imshow(ela_im)
      # plt.show()
      ela_im.save(resaved_filename, 'JPEG')

      return ela_im


   def detect_edges(self, path):
      image = Image.open(path)   
      image = image.convert("L") #Converting to greyscale
      image = image.filter(ImageFilter.FIND_EDGES)
      image = np.array(image.resize((256,256)))
      image = np.reshape(image, (256, 256))
      edge_im = Image.fromarray(image)
      # plt.figure('Edge Map')
      # plt.imshow(image, cmap='gray', aspect='equal')
      # plt.show()
      edge_im.save(resaved_filename, 'JPEG')
      return edge_im

   def luminance_gradient(self, path):
      resaved_filename = os.getcwd()+'/media/luminance_gradient.tiff'
      img = cv.imread(path,0)
      sobelx = cv.Sobel(img,cv.CV_64F,1,0,ksize=15)
      image = Image.fromarray(sobelx).resize((300,300))
      #if image.mode == "F":
       #  image = image.convert('RGB') 
      image.save(resaved_filename,'tiff')
      return image

      # plt.figure('Luminance Gradient')
      # plt.imshow(np.array(image), cmap='gray', aspect='equal')
      # plt.show()

   def noise_analysis(self, path, quality, intensity):
      filename = path
      resaved_filename = 'tempresaved.jpg'
      
      im = Image.open(filename).convert('L')
      im.save(resaved_filename, 'JPEG', quality = quality)
      resaved_im = Image.open(resaved_filename)
      
      na_im = ImageChops.difference(im, resaved_im)
      
      extrema = na_im.getextrema()
      max_diff = max([ex for ex in extrema])
      if max_diff == 0:
         max_diff = 1      
      na_im = ImageEnhance.Brightness(na_im).enhance(intensity)
      return na_im

   def apply_na(self, file_path, sl=50):
      intensity=sl
      na=self.noise_analysis(file_path, 90, intensity)
      na.save(resaved_filename, 'JPEG')
      return na
