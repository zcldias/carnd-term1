
# coding: utf-8

# # Self-Driving Car Engineer Nanodegree
# 
# 
# ## Project: **Finding Lane Lines on the Road** 
# ***
# In this project, you will use the tools you learned about in the lesson to identify lane lines on the road.  You can develop your pipeline on a series of individual images, and later apply the result to a video stream (really just a series of images). Check out the video clip "raw-lines-example.mp4" (also contained in this repository) to see what the output should look like after using the helper functions below. 
# 
# Once you have a result that looks roughly like "raw-lines-example.mp4", you'll need to get creative and try to average and/or extrapolate the line segments you've detected to map out the full extent of the lane lines.  You can see an example of the result you're going for in the video "P1_example.mp4".  Ultimately, you would like to draw just one line for the left side of the lane, and one for the right.
# 
# In addition to implementing code, there is a brief writeup to complete. The writeup should be completed in a separate file, which can be either a markdown file or a pdf document. There is a [write up template](https://github.com/udacity/CarND-LaneLines-P1/blob/master/writeup_template.md) that can be used to guide the writing process. Completing both the code in the Ipython notebook and the writeup template will cover all of the [rubric points](https://review.udacity.com/#!/rubrics/322/view) for this project.
# 
# ---
# Let's have a look at our first image called 'test_images/solidWhiteRight.jpg'.  Run the 2 cells below (hit Shift-Enter or the "play" button above) to display the image.
# 
# **Note: If, at any point, you encounter frozen display windows or other confounding issues, you can always start again with a clean slate by going to the "Kernel" menu above and selecting "Restart & Clear Output".**
# 
# ---

# **The tools you have are color selection, region of interest selection, grayscaling, Gaussian smoothing, Canny Edge Detection and Hough Tranform line detection.  You  are also free to explore and try other techniques that were not presented in the lesson.  Your goal is piece together a pipeline to detect the line segments in the image, then average/extrapolate them and draw them onto the image for display (as below).  Once you have a working pipeline, try it out on the video stream below.**
# 
# ---
# 
# <figure>
#  <img src="examples/line-segments-example.jpg" width="380" alt="Combined Image" />
#  <figcaption>
#  <p></p> 
#  <p style="text-align: center;"> Your output should look something like this (above) after detecting line segments using the helper functions below </p> 
#  </figcaption>
# </figure>
#  <p></p> 
# <figure>
#  <img src="examples/laneLines_thirdPass.jpg" width="380" alt="Combined Image" />
#  <figcaption>
#  <p></p> 
#  <p style="text-align: center;"> Your goal is to connect/average/extrapolate line segments to get output like this</p> 
#  </figcaption>
# </figure>

# **Run the cell below to import some packages.  If you get an `import error` for a package you've already installed, try changing your kernel (select the Kernel menu above --> Change Kernel).  Still have problems?  Try relaunching Jupyter Notebook from the terminal prompt.  Also, consult the forums for more troubleshooting tips.**  

# ## Import Packages

# In[1]:


#importing some useful packages
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
import cv2
import imageio
imageio.plugins.ffmpeg.download()
get_ipython().run_line_magic('matplotlib', 'inline')
# Importing some useful packages

pre_left_m = None
pre_left_b = None
pre_right_m = None
pre_right_b = None


# ## Read in an Image

# In[2]:


#reading in an image

image = mpimg.imread('test_images/solidWhiteRight.jpg')

#printing out some stats and plotting
print('This image is:', type(image), 'with dimensions:', image.shape)
plt.imshow(image)  # if you wanted to show a single color channel image called 'gray', for example, call as plt.imshow(gray, cmap='gray')


# ## Ideas for Lane Detection Pipeline

# **Some OpenCV functions (beyond those introduced in the lesson) that might be useful for this project are:**
# 
# `cv2.inRange()` for color selection  
# `cv2.fillPoly()` for regions selection  
# `cv2.line()` to draw lines on an image given endpoints  
# `cv2.addWeighted()` to coadd / overlay two images
# `cv2.cvtColor()` to grayscale or change color
# `cv2.imwrite()` to output images to file  
# `cv2.bitwise_and()` to apply a mask to an image
# 
# **Check out the OpenCV documentation to learn about these and discover even more awesome functionality!**

# ## Helper Functions

# Below are some helper functions to help get you started. They should look familiar from the lesson!

# In[3]:


import math

def bgr2hsv(img):
    """
    Convert image from BGR to HSV color space.
    Note: if use this function, do not use grayscale
    anymore.
    """
    return cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

def grayscale(img):
    """
    Applies the Grayscale transform
    This will return an image with only one color channel
    but NOTE: to see the returned image as grayscale
    you should call plt.imshow(gray, cmap='gray')
    """
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
def canny(img, low_threshold, high_threshold):
    """Applies the Canny transform"""
    return cv2.Canny(img, low_threshold, high_threshold)

def gaussian_blur(img, kernel_size):
    """Applies a Gaussian Noise kernel"""
    return cv2.GaussianBlur(img, (kernel_size, kernel_size), 0)

def get_yellow_and_white(img):
    '''
    Filter the white and yellow color from the image.
    As they are in this project, white and yellow are 
    universally used as the lane line color
    Function obtained from:
    https://github.com/MehdiSv/FindLanes
    '''
    yellow_min = np.array([65, 80, 80], np.uint8)
    yellow_max = np.array([105, 255, 255], np.uint8)
    yellow_mask = cv2.inRange(img, yellow_min, yellow_max)

    white_min = np.array([0, 0, 200], np.uint8)
    white_max = np.array([255, 80, 255], np.uint8)
    white_mask = cv2.inRange(img, white_min, white_max)

    img = cv2.bitwise_and(img, img, mask=cv2.bitwise_or(yellow_mask, white_mask))
    return img

def region_of_interest(img, vertices):
    """
    Applies an image mask.
    Only keeps the region of the image defined by the polygon
    formed from 'vertices'. The rest of the image is set to black.
    """
    # Defining a blank mask to start with
    mask = np.zeros_like(img)   
    
    # Defining a 3 channel or 1 channel color to fill the mask with depending on the input image
    if len(img.shape) > 2:
        channel_count = img.shape[2]  # i.e. 3 or 4 depending on your image
        ignore_mask_color = (255,) * channel_count
    else:
        ignore_mask_color = 255
        
    # Filling pixels inside the polygon defined by "vertices" with the fill color    
    cv2.fillPoly(mask, vertices, ignore_mask_color)
    
    # Returning the image only where mask pixels are nonzero
    masked_image = cv2.bitwise_and(img, mask)
    return masked_image


def draw_lines(img, lines, color=[255, 0, 0], thickness=10):
    """
    NOTE: this is the function you might want to use as a starting point once you want to 
    average/extrapolate the line segments you detect to map out the full
    extent of the lane (going from the result shown in raw-lines-example.mp4
    to that shown in P1_example.mp4).  
    
    Think about things like separating line segments by their 
    slope ((y2-y1)/(x2-x1)) to decide which segments are part of the left
    line vs. the right line.  Then, you can average the position of each of 
    the lines and extrapolate to the top and bottom of the lane.
    
    This function draws 'lines' with 'color' and 'thickness'.    
    Lines are drawn on the image inplace (mutates the image).
    If you want to make the lines semi-transparent, think about combining
    this function with the weighted_img() function below
    """
    global pre_left_m, pre_left_b, pre_right_m, pre_right_b
    # Change this number to non-zero for temporal smoothing
    prev_ratio = 0.0

    # Create placeholders for slope(m) and intercept(b) for the left line and right line
    left_m = []
    left_b = []
    right_m = []
    right_b = []
    
    # Define the min value for y to find the top points for line drawing
    left_y_min = img.shape[0]
    right_y_min = img.shape[0]
    
    # Go through line by line
    for line in lines:
        for x1,y1,x2,y2 in line:
            # Protect against "divide by zero"
            if(abs(x2 - x1) < 1e-3):
                continue
            # Get the slope and intercept of the current line
            m = (y2 - y1)/(x2 - x1)
            b = y2 - m * x2
            '''
            Check the slope range (experimental values), point location,
            and the intercept at the x=0 or x=x_max (lane line should 
            intercepts with the bottom of the frame, not side)
            '''
            # Left lane
            if(m <= -0.5 and 
               m >= -0.9 and 
               b >= img.shape[0] and
               x1 <= img.shape[1]/2 and
               x2 <= img.shape[1]/2):
                # Save the slope and the intercept
                left_m.append(m)
                left_b.append(b)

            # Right lane
            elif(m >= 0.5 and 
                 m <= 0.9 and 
                 m*img.shape[1] + b >= img.shape[0] and
                 x1 >= img.shape[1]/2 and
                 x2 >= img.shape[1]/2):
                # Save the slope and the intercept
                right_m.append(m)
                right_b.append(b)

            # Uncomment the next line to draw the "pre-processd" lines
            # cv2.line(img, (x1, y1), (x2, y2), [0, 0, 255], thickness)

    # If we found any lines
    if(len(left_m) > 0):
        # Get the average slope and intercept 
        left_avg_m = np.mean(left_m)
        left_avg_b = np.mean(left_b)
        # Temporal smoothing
        if(pre_left_m is not None):
            left_avg_m = prev_ratio * pre_left_m + (1 - prev_ratio) * left_avg_m
            left_avg_b = prev_ratio * pre_left_b + (1 - prev_ratio) * left_avg_b
        # Get the x value for the top point
        left_x_min =  (img.shape[0]*3/5 - left_avg_b) / left_avg_m
        # Get the x value for the bottom point (draw all the way to bottom)
        left_x_max =  (img.shape[0] - left_avg_b) / left_avg_m
        # Draw the left line
        cv2.line(img, (int(left_x_min), int(img.shape[0]*3/5)), (int(left_x_max), img.shape[0]), color, thickness)
        pre_left_m = left_avg_m
        pre_left_b = left_avg_b
        
    if(len(right_m) > 0):
        # Get the average slope and intercept 
        right_avg_m = np.mean(right_m)
        right_avg_b = np.mean(right_b)
        # Temporal smoothing
        if(pre_right_m is not None):
            right_avg_m = prev_ratio * pre_right_m + (1 - prev_ratio) * right_avg_m
            right_avg_b = prev_ratio * pre_right_b + (1 - prev_ratio) * right_avg_b
        # Get the x value for the top point
        right_x_min = (img.shape[0]*3/5 - right_avg_b) / right_avg_m
        # Get the x value for the bottom point (draw all the way to bottom)
        right_x_max = (img.shape[0] - right_avg_b) / right_avg_m
        # Draw the right line
        cv2.line(img, (int(right_x_min), int(img.shape[0]*3/5)), (int(right_x_max), img.shape[0]), color, thickness)
        pre_right_m = right_avg_m
        pre_right_b = right_avg_b

def hough_lines(img, rho, theta, threshold, min_line_len, max_line_gap):
    """
    'img' should be the output of a Canny transform.
    
    Returns an image with hough lines drawn.
    """
    lines = cv2.HoughLinesP(img, rho, theta, threshold, np.array([]), 
                            minLineLength=min_line_len, maxLineGap=max_line_gap)
    line_img = np.zeros([img.shape[0], img.shape[1], 3], dtype=np.uint8)
    draw_lines(line_img, lines)
    return line_img

# Python 3 has support for cool math symbols.

def weighted_img(img, initial_img, α=0.8, β=1.0, λ=0.0):
    """
    'img' is the output of the hough_lines(), An image with lines drawn on it.
    Should be a blank image (all black) with lines drawn on it.
    
    'initial_img' should be the image before any processing.
    
    The result image is computed as follows:
    
    initial_img * α + img * β + λ
    NOTE: initial_img and img must be the same shape!
    """
    return cv2.addWeighted(initial_img, α, img, β, λ)


# ## Test Images
# 
# Build your pipeline to work on the images in the directory "test_images"  
# **You should make sure your pipeline works well on these images before you try the videos.**

# In[4]:


import os
os.listdir("test_images/")


# ## Build a Lane Finding Pipeline
# 
# 

# Build the pipeline and run your solution on all test_images. Make copies into the `test_images_output` directory, and you can use the images in your writeup report.
# 
# Try tuning the various parameters, especially the low and high Canny thresholds as well as the Hough lines parameters.

# In[5]:


# Parameters needed
kernel_size = 3
low_threshold = 50
high_threshold = 150
rho = 1
theta = np.pi/100
threshold = 15
min_line_len = 20
max_line_gap = 50

def lane_line(image):
    #gray = grayscale(image)
    hsv = bgr2hsv(image)
    blur = gaussian_blur(hsv, kernel_size)
    
    yellow_min = np.array([65, 80, 80], np.uint8)
    yellow_max = np.array([105, 255, 255], np.uint8)
    yellow_mask = cv2.inRange(blur, yellow_min, yellow_max)

    white_min = np.array([0, 0, 200], np.uint8)
    white_max = np.array([255, 80, 255], np.uint8)
    white_mask = cv2.inRange(blur, white_min, white_max)

    blur = cv2.bitwise_and(blur, blur, mask=cv2.bitwise_or(yellow_mask, white_mask))
    
    edges = canny(blur, low_threshold, high_threshold)
    height = image.shape[0]
    width = image.shape[1]
    vertices = np.array([[(0,height),(width*2/5, height*3/5), 
                          (width*3/5, height*3/5), (width,height)]], dtype=np.int32)
    masked_edges = region_of_interest(edges, vertices)
    line_image = hough_lines(masked_edges, rho, theta, threshold, min_line_len, max_line_gap)
    lines_edges = weighted_img(line_image, image)
    return lines_edges

# Try on the test images
directory = "test_images/"
for file in os.listdir(directory):
    image = mpimg.imread(os.path.join(directory, file))
    lines_edges = lane_line(image)
    plt.figure(figsize=(8,6))
    plt.imshow(lines_edges)
    plt.title(file)
    plt.show()


# ## Test on Videos
# 
# You know what's cooler than drawing lanes over images? Drawing lanes over video!
# 
# We can test our solution on two provided videos:
# 
# `solidWhiteRight.mp4`
# 
# `solidYellowLeft.mp4`
# 
# **Note: if you get an import error when you run the next cell, try changing your kernel (select the Kernel menu above --> Change Kernel). Still have problems? Try relaunching Jupyter Notebook from the terminal prompt. Also, consult the forums for more troubleshooting tips.**
# 
# **If you get an error that looks like this:**
# ```
# NeedDownloadError: Need ffmpeg exe. 
# You can download it by calling: 
# imageio.plugins.ffmpeg.download()
# ```
# **Follow the instructions in the error message and check out [this forum post](https://discussions.udacity.com/t/project-error-of-test-on-videos/274082) for more troubleshooting tips across operating systems.**

# In[6]:


# Import everything needed to edit/save/watch video clips
from moviepy.editor import VideoFileClip
from IPython.display import HTML


# In[7]:


def process_image(image):
    # Use lane_line() as defined above
    return lane_line(image)


# Let's try the one with the solid white lane on the right first ...

# In[8]:


white_output = 'white.mp4'
clip1 = VideoFileClip("test_videos/solidWhiteRight.mp4")
white_clip = clip1.fl_image(process_image) #NOTE: this function expects color images!!
get_ipython().run_line_magic('time', 'white_clip.write_videofile(white_output, audio=False)')


# Play the video inline, or if you prefer find the video in your filesystem (should be in the same directory) and play it in your video player of choice.

# In[9]:


HTML("""
<video width="960" height="540" controls>
  <source src="{0}">
</video>
""".format(white_output))


# ## Improve the draw_lines() function
# 
# **At this point, if you were successful with making the pipeline and tuning parameters, you probably have the Hough line segments drawn onto the road, but what about identifying the full extent of the lane and marking it clearly as in the example video (P1_example.mp4)?  Think about defining a line to run the full length of the visible lane based on the line segments you identified with the Hough Transform. As mentioned previously, try to average and/or extrapolate the line segments you've detected to map out the full extent of the lane lines. You can see an example of the result you're going for in the video "P1_example.mp4".**
# 
# **Go back and modify your draw_lines function accordingly and try re-running your pipeline. The new output should draw a single, solid line over the left lane line and a single, solid line over the right lane line. The lines should start from the bottom of the image and extend out to the top of the region of interest.**

# Now for the one with the solid yellow lane on the left. This one's more tricky!

# In[10]:


yellow_output = 'yellow.mp4'
clip2 = VideoFileClip("test_videos/solidYellowLeft.mp4")
yellow_clip = clip2.fl_image(process_image)
get_ipython().run_line_magic('time', 'yellow_clip.write_videofile(yellow_output, audio=False)')


# In[11]:


HTML("""
<video width="960" height="540" controls>
  <source src="{0}">
</video>
""".format(yellow_output))


# ## Writeup and Submission
# 
# If you're satisfied with your video outputs, it's time to make the report writeup in a pdf or markdown file. Once you have this Ipython notebook ready along with the writeup, it's time to submit for review! Here is a [link](https://github.com/udacity/CarND-LaneLines-P1/blob/master/writeup_template.md) to the writeup template file.
# 

# ## Optional Challenge
# 
# Try your lane finding pipeline on the video below.  Does it still work?  Can you figure out a way to make it more robust?  If you're up for the challenge, modify your pipeline so it works with this video and submit it along with the rest of your project!

# In[12]:


challenge_output = 'extra.mp4'
clip2 = VideoFileClip("test_videos/challenge.mp4")
challenge_clip = clip2.fl_image(process_image)
get_ipython().run_line_magic('time', 'challenge_clip.write_videofile(challenge_output, audio=False)')


# In[13]:


HTML("""
<video width="960" height="540" controls>
  <source src="{0}">
</video>
""".format(challenge_output))

