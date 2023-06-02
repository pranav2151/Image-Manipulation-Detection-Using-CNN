import datetime
from django.shortcuts import render, redirect, HttpResponseRedirect
import asyncio
from multiprocessing import Pool
import numpy as np
import subprocess

import streamlit as st
import sys
import os
from website.ImageForgeryDetection.FakeImageDetector import FID
##from website.videoForgeryDetection.videoFunctions import *
from django.core.files.storage import FileSystemStorage

import website.ImageForgeryDetection.double_jpeg_compression as djc  # ADD1
import website.ImageForgeryDetection.noise_variance as nvar
import website.ImageForgeryDetection.copy_move_cfa as cfa
import website.ImageForgeryDetection.copy_move_sift as sift

from optparse import OptionParser
from json import dumps
from pdf2image import convert_from_path

from website.VideoForgeryDetection.detect_video import detect_video_forgery
from PIL import Image
from PIL.ExifTags import TAGS

# Create your views here.

fileurl = ''
inputImageUrl = ''
result = {}
inputVideoUrl = ''
fileVideoUrl = ''
infoDict = {}
inputImage=''


def getMetaData(path):
    global infoDict
    # CODE for metadata starts
    imgPath = path
    exeProcess = "hachoir-metadata"
    process = subprocess.Popen([exeProcess, imgPath],
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               universal_newlines=True)

    for tag in process.stdout:
        line = tag.strip().split(':')
        infoDict[line[0].strip()] = line[-1].strip()

    for k, v in infoDict.items():
        print(k, ':', v)
    if "Metadata" in infoDict.keys():
        del infoDict["Metadata"]
    # CODE for metadata ends

def index(request):
    return render(request, "index.html")


def image(request):
    return render(request, "image.html")



def runAnalysis(request):
    global fileurl, inputImageUrl, result, infoDict,inputImage
    print('request---------------------------',request.POST.get('run'))
    
    if request.POST.get('run'):
            inputImage=''
            if inputImageUrl=='' or 'input_image' in request.FILES:   
                print('request.FILES---------------------------',request.FILES)
                inputImg = request.FILES['input_image'] if 'input_image' in request.FILES else None
                print('inputImg---------------------------',inputImg)
                if inputImg:
                    fs = FileSystemStorage()
                    file = fs.save(inputImg.name, inputImg)
                    fileurl =  os.getcwd() +fs.url(file)
                    inputImageUrl = '../media/' + inputImg.name
            elif inputImageUrl!='':
                #inputImageUrl = inputImageUrl
                fileurl = os.getcwd() + '/media/' + os.path.basename(inputImageUrl)

            # getMetaData(fileurl)
            print('fileurl---------------------------',fileurl)
            res = FID().predict_result(fileurl)

            if res[0] == 'Authentic':
                result = {'type': res[0], 'confidence': res[1]}
                inputImage=inputImageUrl
                inputImageUrl=''

                return render(request, "image.html",
                              {'result': result, 'input_image': inputImage, 'metadata': infoDict.items()})

            elif res[0] == 'Forged':
                cmd = OptionParser("usage: %prog image_file [options]")
                cmd.add_option('', '--imauto', help='Automatically search identical regions. (default: %default)', default=1)
                cmd.add_option('', '--imblev',help='Blur level for degrading image details. (default: %default)', default=8)
                cmd.add_option('', '--impalred',help='Image palette reduction factor. (default: %default)', default=15)
                cmd.add_option('', '--rgsim', help='Region similarity threshold. (default: %default)', default=5)
                cmd.add_option('', '--rgsize',help='Region size threshold. (default: %default)', default=1.5)
                cmd.add_option('', '--blsim', help='Block similarity threshold. (default: %default)',default=200)
                cmd.add_option('', '--blcoldev', help='Block color deviation threshold. (default: %default)', default=0.2)
                cmd.add_option('', '--blint', help='Block intersection threshold. (default: %default)', default=0.2)
                opt, args = cmd.parse_args()
                if not args:
                    cmd.print_help()
                    sys.exit()
                im_str = args[0]

                print('\nRunning double jpeg compression detection...\n')
                double_compressed = djc.detect(fileurl)      # check type of forgery
                if(double_compressed): compression= 'Double compressed'
                else: compression= 'Single compressed'

                print('\nRunning noise variance inconsistency detection...')
                noise_forgery = nvar.detect(fileurl)

                if(noise_forgery): noise_var=1
                else: noise_var= 0

                # print('\nRunning CFA artifact detection...\n')
                # identical_regions_cfa = cfa.detect(fileurl, opt, args)
                # identical_regions = dumps(identical_regions_cfa)
                # print(identical_regions_cfa, 'identical regions detected')

                res= FID().predict_result(fileurl) 
                
                result = {'type': res[0], 'confidence': res[
                    1], 'compression': compression, 'noise_var': noise_var}
                inputImage=inputImageUrl
                inputImageUrl=''
                return render(request, "image.html",
                              {'result': result, 'input_image': inputImage, 'metadata': infoDict.items()})



def getImages(request):
    global fileurl, inputImageUrl, result,inputImage
    outputImageUrl = "../media/tempresaved.jpg"
    if request.POST.get('mask'):
        FID().genMask(fileurl)
        return render(request, "image.html", {'url': outputImageUrl, 'input_image': inputImage, 'result': result,
                                              'metadata': infoDict.items()})

    if request.POST.get('ela'):
        FID().show_ela(fileurl)
        return render(request, "image.html", {'url': outputImageUrl, 'input_image': inputImage, 'result': result,
                                              'metadata': infoDict.items()})

    if request.POST.get('edge_map'):
        FID().detect_edges(fileurl)
        return render(request, "image.html", {'url': outputImageUrl, 'input_image': inputImage, 'result': result,
                                              'metadata': infoDict.items()})

    if request.POST.get('lum_gradiend'):
        outputImageUrl = "../media/luminance_gradient.tiff"
        FID().luminance_gradient(fileurl)
        return render(request, "image.html", {'url': outputImageUrl, 'input_image': inputImage, 'result': result,
                                              'metadata': infoDict.items()})

    if request.POST.get('na'):
        FID().apply_na(fileurl)
        return render(request, "image.html", {'url': outputImageUrl, 'input_image': inputImage, 'result': result,
                                              'metadata': infoDict.items()})
    if request.POST.get('copy_move_sift'):
        cmsift = sift.CopyMoveSIFT(fileurl)
        return render(request, "image.html", {'url': outputImageUrl, 'input_image': inputImage, 'result': result,
                                              'metadata': infoDict.items()})
