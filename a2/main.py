#!/usr/bin/python3
#
# Removal of periodic features using the FFT
#
# Use Python 3+ with these packages: numpy, PyOpenGL, Pillow, glfw
#
# DO NOT IMPORT OR USE ANY ADDITIONAL LIBRARIES.


import sys, os, math

try: # NumPy
  import numpy as np
except:
  print( 'Error: NumPy has not been installed.' )
  sys.exit(0)

try: # Pillow
  from PIL import Image, ImageOps
except:
  print( 'Error: Pillow has not been installed.' )
  sys.exit(0)

try: # PyOpenGL
  #from OpenGL.GLUT import *
  from OpenGL.GL import *
  from OpenGL.GLU import *
  
except:
  print( 'Error: PyOpenGL has not been installed.' )
  sys.exit(0)

try: # GLFW
  import glfw
except:
  print( 'Error: GLFW has not been installed.' )
  sys.exit(0)


# Globals

windowWidth  = 1000 # window dimensions (not image dimensions)
windowHeight =  800

showMagnitude = True            # for the FT, show the magnitude.  Otherwise, show the phase
doHistoEq = False               # do histogram equalization on the FT to make features more obvious

texID = None                    # for OpenGL

zoom = 1.0                      # amount by which to zoom images
translate = (0.0,0.0)           # amount by which to translate images


# Image

imageDir      = 'images'
imageFilename = 'ecg-01.png'
imagePath     = os.path.join( imageDir, imageFilename )

image    = None                 # the image as a 2D np.array
imageFT  = None                 # the image's FT as a 2D np.array

gridImage   = None              # the grid, isolated from the image
gridImageFT = None              # the grid's FT

resultImage = None              # the final image


# Remove the grid from the global 'image'.  Return the result image
# AND a list of [ [angle1,distance1], [angle2,distance2] ] describing
# the two principal grid lines.
#
# The angle is the angle, in degrees, of the grid line
# counterclockwise from the horizontal.
#
# The distance is the distance from the origin, in pixels, of the
# first peak in the Fourier Transform corresponding to the lines at
# the given angle.  This will later be used to calculate the line
# spacing.
#
# Do the following in the compute() function:
#
#   1. Compute the FT of the image.  Store it in 'imageFT'.
#
#   2. Compute and store the FT magnitudes.  Find the maximum
#      magnitude, EXCLUDING the DC component in [0,0]. 
#
#   3. Set to zero the components of 'imageFT' that have magnitude
#      less than 40% the maximum magnitude.  Store this new FT in
#      'gridImageFT'.  Record in a list the (x,y) locations of the
#      non-zero magnitudes of 'gridImageFT'.
#
#   4. From the locations of the non-zero magnitudes, find the angles
#      of the two principal grid lines and, for each such line, find
#      the distance of the closest non-zero magnitude to the origin.
#
#      THIS IS DIFFICULT and can be left until you have zeroed the grid
#      line pixels as described in Step 6.
#
#   5. Apply the inverse FT to 'gridImageFT' to get 'gridImage'.
#
#   6. For each (x,y) location in 'gridImage' that has a bright pixel
#      of value > 16 (i.e. is one of the grid lines), set the
#      corresponding pixel in the original 'image' to the average of
#      the pixels on either side of the grid line that are not also
#      grid line pixels.  Do not modify 'image'; instead, store your
#      result in 'resultImage'.
#
#      FINDING THE AVERAGE IS DIFFICULT, so first set the grid line
#      pixels to zero and debug your code to make sure that this is
#      working.  Only after this is working should you try to set the
#      grid line pixels to the average from either side.  You will need 
#      to know the angles from Step 4 to do this.
#
# Test your code on all files in the 'images' directory.  Debug using the 'small.png' file.
#
# DO NOT IMPORT OR USE ANY ADDITIONAL LIBRARIES.
#
# DO NOT USE NUMPY FOR ANYTHING BUT THE FOLLOWING OPERATIONS:
#     
#     np.absolute
#     np.complex_
#     np.imag
#     np.max
#     np.median
#     np.real
#     np.sqrt
#     np.sqrt
#     np.tan
#     np.vectorize
#     np.zeros
#
# In the compute() function below, you should always iterate over the
# image in your own code, rather than call some NumPy function to do
# the iteration for you.


def compute():

  global image, imageFT, gridImage, gridImageFT, resultImage

  #get height and width of the image
  height = image.shape[0]
  width  = image.shape[1]

  # Forward FT
  print( '1. compute FT' )
  imageFT = forwardFT(image)

  # Compute magnitudes and find the maximum (excluding the DC component)
  print( '2. computing FT magnitudes' )
  #create array to store magnitudes
  magnitudes = np.zeros((height, width))
  #loop through to extract magnitudes
  for y in range(height):
    for x in range(width):
      #calculate the magnitude, place in magnitude array
      a = 2 * np.real(imageFT[y][x])
      b = -2 * np.imag(imageFT[y][x])
      magnitudes[y][x] = np.sqrt(a*a + b*b)

  #extract the maximum
  #save DC component to restore later
  temp = magnitudes[0][0]
  #set DC to 0
  magnitudes[0][0] = 0
  #get the maximum of the array
  max = np.max(magnitudes)
  #restore DC component
  magnitudes[0][0] = temp
  
  # Zero the components that are less than 40% of the max

  print( '3. removing low-magnitude components' )

  if gridImageFT is None:
    gridImageFT = np.zeros( (height,width), dtype=np.complex_ )

  #array for none-zero
  nonzero = np.zeros((height, width))
  #loop to zero componentents that are less than 40% threshold
  for y in range(height):
    for x in range(width):
      #set to 0 if below threshold
      if magnitudes[y][x] < 0.4 * max:
        gridImageFT[y][x] = 0
      #keep value if above threshold
      else:
        gridImageFT[y][x] = imageFT[y][x]
        #track that certain value is non-zero
        nonzero[y][x] = 1
        

  # Find (angle, distance) to each peak
  #
  # lines = [ (angle1,distance1), (angle2,distance2) ]
  data = []

  print( '4. finding angles and distances of grid lines' )
  #ft lines go through middle of grid so only need to look at half the grid, angle and spaceing are identical on either side
  #this cuts the computation time in half for this step
  for y in range(int(height/2)):
    for x in range(width):
      #check if value is none zero, if zero do nothing
      if nonzero[y][x]:
        angle = None
        distance = None
        #go through each bottom quadrant seperately since angle needs to be calculated differently for each
        if x > width/2:
          angle = np.arctan2(y*width/height, x-width) * 180/(np.pi)
          #get distance to center
          distance = np.sqrt(y*y + (x-width)*(x-width)) 
        else:
          angle = np.arctan2(y*width/height, x) * 180/(np.pi)
          distance = np.sqrt(y*y+ x*x)
        
        #make sure angle is below 180, can manipulate angle since angle +- 180 gives the desired result
        if angle >= 180:  
          angle = angle - 180

        #remove the origin since it skews median calculation, also drop items close to origin
        if distance > 10:
          data.append((angle, distance))
  
  #sort list by angle
  data = sorted(data)

  #get smallest angle 
  smallestAngle = data[0][0]
  index = 0
  
  #loop to find where to split sorted angle list
  for x in range(len(data)):
    #give a range that angle should be similar to, I gave threshold of 10 degrees
    if (data[x][0] - smallestAngle) > 10:
      index = x
      break

  
  #split based off of where the angle jumps upward
  #this gives two clusters, one for each line
  line1 = data[:index]
  line2 = data[index:]

  #calculate median values for each line, use median angle as answer
  #median is used instead of mean since an outlier could skew mean calculation
  med1 = np.median(line1, axis = 0)
  med2 = np.median(line2, axis = 0)

  #assign angle1 and 2 to the median value of their lines
  angle1 = med1[0]
  angle2 = med2[0]
  
  
  #sort by distance, do this so i can filter out points that are on top of each others for distance calculations
  line1.sort(key=lambda x:x[1])
  line2.sort(key=lambda x:x[1])
  
  #get median distance between points, ignore duplicate points distance
 
  #indexes of each element when iterating through
  index = 0
  #arrays to put data into
  distance_cluster_1 = []
  distanceArray1 = []
  
  #loop through line 1 distance values
  while index < (len(line1)-1):
    #temporary array needed to calculate mean of duplicate points
    temp = []
    #see if point in same cluster, same cluster if distance values differ by less than 2, greater than 2 means they are different clusters

    if line1[index+1][1] - line1[index][1] > 2:
      #check if temp is empty, if not empty calculate mean distance
      if len(temp) != 0:
        
        #add median distance
        distance_cluster_1.append(np.median(temp))
        #empty array so it can be used for next cluster
        temp.clear()
      else:
        #if temp is empty, add distance value to array
        distance_cluster_1.append(line1[index][1])
    else:
      #if distance appart is less than 2, add to temp array used to calculate cluster center
      temp.append(line1[index][1])
    #iterate through array
    index = index + 1

  #index for the next loop
  index1 = 0
  #append element closest to origin since loop skips it
  distanceArray1.append(distance_cluster_1[0])
  #this loop calulated distance between each clusters center
  while index1 < (len(distance_cluster_1)-1):
    #get distance between sorted points
    distance = distance_cluster_1[index1+1] - distance_cluster_1[index1]
    #add distance to array
    distanceArray1.append(distance)
    index1 = index1 + 1
  #calculate median distance, use this as output
  #I am assuming median distance is desired not mean since median function was allowed to be used but mean wasnt
  distance1 = np.median(distanceArray1)

  print(distanceArray1)
  #repeat for distance2
  index = 0
  distance_cluster_2 = []
  distanceArray2 = []
  #loop through line 2 distance values
  while index < (len(line2)-1):
    #temporary array needed to calculate mean of duplicate points
    temp = []
    #see if point in same cluster, same cluster if distance values differ by less than 2, greater than 2 means they are different clusters
    if line2[index+1][1] - line2[index][1] > 2:
      if len(temp) != 0:
        total = 0
        counter = 0
        #add mean median distance
        distance_cluster_2.append(np.median(temp))
        #clear array for further use
        temp.clear()
      else:
        #if temp is empty, add distance value to array
        distance_cluster_2.append(line2[index][1])
    else:
      #if distance appart is less than 2, add to temp array used to calculate cluster center
      temp.append(line2[index][1])
    index = index + 1

  #index for new loop
  index2 = 0

  #append element closest to origin since loop skips it
  distanceArray2.append(distance_cluster_2[0])
  while index2 < (len(distance_cluster_2)-1):
    #get distance between sorted points
    distance = distance_cluster_2[index2+1] - distance_cluster_2[index2]
    #add distance to array
    distanceArray2.append(distance)
    index2 = index2 + 1
  #calc median distance, use as output
  distance2 = np.median(distanceArray2)
  print(distanceArray2)
  lines = [(angle1,distance1),(angle2,distance2)]
  # Convert back to spatial domain to get a grid-like image

  print( '5. inverse FT' )
  gridImage = inverseFT(gridImageFT)
  if gridImage is None:
    gridImage = np.zeros( (height,width), dtype=np.complex_ )

  # Remove grid image from original image

  print( '6. remove grid' )

  if resultImage is None:
    resultImage = image.copy()
  #explanation of step 6
  #check in perpendicular direction of both angles since we dont know which line the point is on
  #use value which is the smallest since it would come from the direction that is not a grid line
  # I know this since the direction of the grid lines are perpendiclar so looking in either direction at point will 
  # give a line which overlaps a grid line and one that does not, the lesser value is the one that does not overlap the grid line
  
  
  #loop through each pixel
  for y in range(height):
    for x in range(width):
      #only check is grid image vlaue is above 16, since those represnt the grid lines
      if(gridImage[y][x] > 16):
        size = 1
        #variables to say if point on either side of line is valid
        output_1_valid = True
        output_2_valid = True
        #try except statement used to handle out of bounds exceptions,
        #if out of bounds we know that this point is not viable
        #this results in setting the valid value to false for the point in this direction

        try:
          #get points to look for new value at
          x_point = x + size * math.cos(angle1*np.pi/180)
          y_point = y + size * math.sin(angle1*np.pi/180)
          output_1 = image[int(round(y_point,0)),int(round(x_point, 0))]

          #check if gridimage value is greater than 16, which signifies you are looking at a grid pixel
          #if looking at grid pixel look at next pixel instead
          #repeat twice before saying direction is not valid
          if gridImage[int(round(y_point,0)),int(round(x_point, 0))] > 16:
            x_point = x + (size+1) * math.cos(angle1*np.pi/180)
            y_point = y + (size+1) * math.sin(angle1*np.pi/180)
            output_1 = image[int(round(y_point,0)),int(round(x_point, 0))]
          if gridImage[int(round(y_point,0)),int(round(x_point, 0))] > 16:
            x_point = x + (size+2) * math.cos(angle1*np.pi/180)
            y_point = y + (size+2) * math.sin(angle1*np.pi/180)
            output_1 = image[int(round(y_point,0)),int(round(x_point, 0))]
          #statement saying direction is not valid
          if gridImage[int(round(y_point,0)),int(round(x_point, 0))] > 16:
            output_1_valid = False
        except:
          output_1_valid = False
        
        #repeat the code above for the point on other side of line
        #gotten by increaseing angle by pi then calculating the points
        try:
          x_point = x + size * math.cos(angle1*np.pi/180 + np.pi)
          y_point = y + size * math.sin(angle1*np.pi/180 + np.pi)
          output_2 = image[int(round(y_point,0)),int(round(x_point, 0))]
          if gridImage[int(round(y_point,0)),int(round(x_point, 0))] > 16:
            x_point = x + (size+1) * math.cos(angle1*np.pi/180 + np.pi)
            y_point = y + (size+1) * math.sin(angle1*np.pi/180 + np.pi)
            output_2 = image[int(round(y_point,0)),int(round(x_point, 0))]
          if gridImage[int(round(y_point,0)),int(round(x_point, 0))] > 16:
            x_point = x + (size+2) * math.cos(angle1*np.pi/180 + np.pi)
            y_point = y + (size+2) * math.sin(angle1*np.pi/180 + np.pi)
            output_2 = image[int(round(y_point,0)),int(round(x_point, 0))]
          if gridImage[int(round(y_point,0)),int(round(x_point, 0))] > 16:
            output_2_valid = False
        except:
          output_2_valid = False

        #variables for angle1 output and status used to see if the angle can be used
        angle_1_output = 0
        angle_1_status = True

        #if both directions are valid take average of the two values
        if output_1_valid == True and output_2_valid == True:
          angle_1_output = (output_1 + output_2)/2
        #if one direction is valid, use its value
        if output_1_valid == True and output_2_valid == False:
          angle_1_output = output_1
        if output_1_valid == False and output_2_valid == True:
          angle_1_output = output_2
        #if no directions is valid set output to zero and state that angle is not valid
        if output_1_valid == False and output_2_valid == False:
          angle_1_output = 0
          angle_1_status = False

        #repeat the code above for angle2, same logic just using angle 2
        #comment will explain none repeated code
        try:
          x_point = x + size * math.cos(angle2*np.pi/180)
          y_point = y + size * math.sin(angle2*np.pi/180)

          output_1 = image[int(round(y_point,0)),int(round(x_point, 0))]
          if gridImage[int(round(y_point,0)),int(round(x_point, 0))] > 16:
            x_point = x + (size+1) * math.cos(angle2*np.pi/180)
            y_point = y + (size+1) * math.sin(angle2*np.pi/180)
            output_1 = image[int(round(y_point,0)),int(round(x_point, 0))]
          if gridImage[int(round(y_point,0)),int(round(x_point, 0))] > 16:
            x_point = x + (size+2) * math.cos(angle2*np.pi/180)
            y_point = y + (size+2) * math.sin(angle2*np.pi/180)
            output_1 = image[int(round(y_point,0)),int(round(x_point, 0))]
          if gridImage[int(round(y_point,0)),int(round(x_point, 0))] > 16:
            output_1_valid = False
        except:
          output_1_valid = False
        
        try:
          x_point = x + size * math.cos(angle2*np.pi/180 + np.pi)
          y_point = y + size * math.sin(angle2*np.pi/180 + np.pi)
          output_2 = image[int(round(y_point,0)),int(round(x_point, 0))]
          if gridImage[int(round(y_point,0)),int(round(x_point, 0))] > 16:
            x_point = x + (size+1) * math.cos(angle2*np.pi/180 + np.pi)
            y_point = y + (size+1) * math.sin(angle2*np.pi/180 + np.pi)
            output_2 = image[int(round(y_point,0)),int(round(x_point, 0))]
          if gridImage[int(round(y_point,0)),int(round(x_point, 0))] > 16:
            x_point = x + (size+2) * math.cos(angle2*np.pi/180 + np.pi)
            y_point = y + (size+2) * math.sin(angle2*np.pi/180 + np.pi)
            output_2 = image[int(round(y_point,0)),int(round(x_point, 0))]
          if gridImage[int(round(y_point,0)),int(round(x_point, 0))] > 16:
            output_2_valid = False
        except:
          output_2_valid = False

        angle_2_output = 0
        angle_2_status = True

        #if both directions are valid take average of the two values
        if output_1_valid == True and output_2_valid == True:
          angle_2_output = (output_1 + output_2)/2
        #if one direction is valid use its value
        if output_1_valid == True and output_2_valid == False:
          angle_2_output = output_1
        if output_1_valid == False and output_2_valid == True:
          angle_2_output = output_2
          #if neither set point value to 0 and state angle is not valid
        if output_1_valid == False and output_2_valid == False:
          angle_2_output = 0
          angle_2_status = False
        
        #if both are valid choose smaller value
        if angle_1_status == True and angle_2_status == True:
          if angle_1_output < angle_2_output:
            resultImage[y][x] = angle_1_output
          else:
            resultImage[y][x] = angle_2_output
        #if only one angle is valid use its value
        if angle_1_status == False and angle_2_status == True:
          resultImage[y][x] = angle_2_output
        if angle_1_status == True and angle_2_status == False:
          resultImage[y][x] = angle_1_output
        #if neither angle produces a valid value, set resulting image value to 0 
        if angle_1_status == False and angle_2_status == False:
          resultImage[y][x] = 0
      #if not a grid line do not change the value
      else:
        resultImage[y][x] = image[y][x]

  print( 'done' )

  return resultImage, lines


      

# File dialog

haveTK = False

if haveTK:
    import Tkinter, tkFileDialog
    root = Tkinter.Tk()
    root.withdraw()



# Do a forward FT
#
# Input is a 2D numpy array of complex values.
# Output is the same.

def forwardFT( image ):

  return np.fft.fft2( image )



# Do an inverse FT
#
# Input is a 2D numpy array of complex values.
# Output is the same.


def inverseFT( image ):

  return np.fft.ifft2( image )



# Set up the display and draw the current image


def display( window ):

  # Clear window

  glClearColor ( 1, 1, 1, 0 )
  glClear( GL_COLOR_BUFFER_BIT )

  glMatrixMode( GL_PROJECTION )
  glLoadIdentity()

  glMatrixMode( GL_MODELVIEW )
  glLoadIdentity()
  glOrtho( 0, windowWidth, 0, windowHeight, 0, 1 )

  # Set up texturing

  global texID
  
  if texID == None:
    texID = glGenTextures(1)

  glPixelStorei( GL_UNPACK_ALIGNMENT, 1 )
  glBindTexture( GL_TEXTURE_2D, texID )

  glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)
  glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER)
  glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER)
  glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
  glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
  glTexParameterfv(GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, [1,0,0,1] );

  # Images to draw, in rows and columns

  toDraw, rows, cols, maxHeight, maxWidth, scale, horizSpacing, vertSpacing = getImagesInfo()

  for r in range(rows):
    for c in range(cols):
      if toDraw[r][c] is not None:

        if r == 0: # normal image in row 0 
          img = toDraw[r][c]
        else: # FT in column 1
          img = np.fft.fftshift( toDraw[r][c] ) # shift FT so that origin is in centre (just for display)

        height = scale * img.shape[0]
        width  = scale * img.shape[1]

        # Find lower-left corner

        baseX = (horizSpacing + maxWidth ) * c + horizSpacing
        baseY = (vertSpacing  + maxHeight) * (rows-1-r) + vertSpacing

        # Get pixels and draw

        if r == 0: # for images (in row 0), show the real part of each pixel
          show = np.real(img)
        else: # for FT (in column 1), show magnitude or phase
          ak =  2 * np.real(img)
          bk = -2 * np.imag(img)
          if showMagnitude:
            show = np.log( 1 + np.sqrt( ak*ak + bk*bk ) ) # take the log because there are a few very large values (e.g. the DC component)
          else:
            show = np.arctan2( -1 * bk, ak )

          if doHistoEq and c > 0:
            show = histoEq( show ) # optionally, perform histogram equalization on FT image (but this takes time!)

        # Put the image into a texture, then draw it

        max = show.max()
        min = show.min()
        if max == min:
          max = min+1
          
        imgData = np.array( (np.ravel(show) - min) / (max - min) * 255, np.uint8 )

        glTexImage2D( GL_TEXTURE_2D, 0, GL_INTENSITY, img.shape[1], img.shape[0], 0, GL_LUMINANCE, GL_UNSIGNED_BYTE, imgData )

        # Include zoom and translate

        cx     = 0.5 - translate[0]/width
        cy     = 0.5 - translate[1]/height
        offset = 0.5 / zoom

        glEnable( GL_TEXTURE_2D )

        glBegin( GL_QUADS )
        glTexCoord2f( cx-offset, cy-offset )
        glVertex2f( baseX, baseY )
        glTexCoord2f( cx+offset, cy-offset )
        glVertex2f( baseX+width, baseY )
        glTexCoord2f( cx+offset, cy+offset )
        glVertex2f( baseX+width, baseY+height )
        glTexCoord2f( cx-offset, cy+offset )
        glVertex2f( baseX, baseY+height )
        glEnd()

        glDisable( GL_TEXTURE_2D )

        if zoom != 1 or translate != (0,0):
          glColor3f( 0.8, 0.8, 0.8 )
          glBegin( GL_LINE_LOOP )
          glVertex2f( baseX, baseY )
          glVertex2f( baseX+width, baseY )
          glVertex2f( baseX+width, baseY+height )
          glVertex2f( baseX, baseY+height )
          glEnd()

  # Draw image captions

  glColor3f( 0.2, 0.5, 0.7 )
 
  if image is not None:
    baseX = horizSpacing
    baseY = (vertSpacing  + maxHeight) * (rows) + 8
    drawText( baseX, baseY, imageFilename )

  if imageFT is not None:
    baseX = horizSpacing
    baseY = (vertSpacing  + maxHeight) * (rows-2) + vertSpacing - 18
    drawText( baseX, baseY, 'FT of %s' % imageFilename )

  if gridImage is not None:
    baseX = (horizSpacing + maxWidth) * 1 + horizSpacing
    baseY = (vertSpacing  + maxHeight) * rows + 8
    drawText( baseX, baseY, 'extracted grid' )

  if gridImageFT is not None:
    baseX = (horizSpacing + maxWidth) * 1 + horizSpacing
    baseY = (vertSpacing  + maxHeight) * (rows-2) + vertSpacing - 18
    drawText( baseX, baseY, 'FT of extracted grid' )

  if resultImage is not None:
    baseX = (horizSpacing + maxWidth) * 2 + horizSpacing
    baseY = (vertSpacing  + maxHeight) * (rows) + 8
    drawText( baseX, baseY, 'result' )

  # Draw mode information

  str = 'show %s' % ('magnitudes' if showMagnitude else 'phases')
  glColor3f( 0.5, 0.2, 0.4 )
  drawText( windowWidth-len(str)*8-8, 12, str )

  # Done

  glfw.swap_buffers( window )

  

# Get information about how to place the images.
#
# toDraw                       2D array of complex images 
# rows, cols                   rows and columns in array
# maxHeight, maxWidth          max height and width of images
# scale                        amount by which to scale images
# horizSpacing, vertSpacing    spacing between images


def getImagesInfo():

  toDraw = [ [ image,   gridImage,   resultImage   ],
             [ imageFT, gridImageFT, None ] ]

  rows = len(toDraw)
  cols = len(toDraw[0])

  # Find max image dimensions

  maxHeight = 0
  maxWidth  = 0
  
  for row in toDraw:
    for img in row:
      if img is not None:
        if img.shape[0] > maxHeight:
          maxHeight = img.shape[0]
        if img.shape[1] > maxWidth:
          maxWidth = img.shape[1]

  # Scale everything to fit in the window

  minSpacing = 30 # minimum spacing between images

  scaleX = (windowWidth  - (cols+1)*minSpacing) / float(maxWidth  * cols)
  scaleY = (windowHeight - (rows+1)*minSpacing) / float(maxHeight * rows)

  if scaleX < scaleY:
    scale = scaleX
  else:
    scale = scaleY

  maxWidth  = scale * maxWidth
  maxHeight = scale * maxHeight

  # Draw each image

  horizSpacing = (windowWidth-cols*maxWidth)/(cols+1)
  vertSpacing  = (windowHeight-rows*maxHeight)/(rows+1)

  return toDraw, rows, cols, maxHeight, maxWidth, scale, horizSpacing, vertSpacing
  

  
# Equalize the image histogram

def histoEq( pixels ):

  # build histogram

  h = [0] * 256 # counts

  width  = pixels.shape[0]
  height = pixels.shape[1]

  min = pixels.min()
  max = pixels.max()
  if max == min:
    max = min+1

  for i in range(width):
    for j in range(height):
      y = int( (pixels[i,j] - min) / (max-min) * 255 )
      h[y] = h[y] + 1

  # Build T[r] = s

  k = 256.0 / float(width * height) # common factor applied to all entries

  T = [0] * 256 # lookup table
  
  sum = 0
  for i in range(256):
    sum = sum + h[i]
    T[i] = int( math.floor(k * sum) - 1 )
    if T[i] < 0:
      T[i] = 0

  # Apply T[r]

  result = np.empty( pixels.shape )

  for i in range(width):
    for j in range(height):
      y = int( (pixels[i,j] - min) / (max - min) * 255 )
      result[i,j] = T[y]

  return result
  

# Handle keyboard input

def keyCallback( window, key, scancode, action, mods ):

  global image, imageFT, gridImage, gridImageFT, resultImage, showMagnitude, doHistoEq, imageFilename, zoom, translate

  if action == glfw.PRESS:
    
    if key == glfw.KEY_ESCAPE:  # quit upon ESC
      sys.exit(0)

    elif key == glfw.KEY_L: # load an image

      if haveTK:
          imagePath = tkFileDialog.askopenfilename( initialdir = imageDir )
          if imagePath:
            image = loadImage( imagePath )
            imageFilename = os.path.basename( imagePath )
            imageFT = None
            gridImage = None
            gridImageFT = None
            resultImage = None

    elif key == glfw.KEY_M: # toggle magnitude/phase display
      showMagnitude = not showMagnitude

    elif key == glfw.KEY_H: # toggle histogram equalization
      doHistoEq = not doHistoEq

    elif key == glfw.KEY_Z: # zero the zoom and translation
      zoom = 1
      translate = (0,0)

    elif key == glfw.KEY_C: # compute

      resultImage, lines = compute()
      print( 'Grid lines:' )
      for line in lines:
        print( '  angle %.1f, distance %.1f' % (line[0],line[1]) )

    elif key == glfw.KEY_DOWN:  # forward FT
      forwardFT_all()

    elif key == glfw.KEY_UP: # backward FT
      inverseFT_all()

    elif key == glfw.KEY_SLASH: # help (/ or ?)

      print( '''keys:
             c  compute the solution
             m  toggle between magnitude and phase in the FT  
             h  toggle histogram equalization in the FT  
             l  load image
    down arrow  forward transform
      up arrow  inverse transform
                translate with left mouse dragging
                zoom with right mouse draggin up/down
             z  reset the translation and zoom''' )



# Do a forward FT to image


def forwardFT_all():

  global image, imageFT

  if image is not None:
    imageFT = forwardFT( image )



# Do an inverse FT to imageFT


def inverseFT_all():

  global image, imageFT

  if imageFT is not None: 
    image = inverseFT( imageFT )


    
# Load an image
#
# Return the image as a 2D numpy array of complex_ values.


def loadImage( path ):

  try:
    img = Image.open( path ).convert( 'L' ).transpose( Image.FLIP_TOP_BOTTOM )
  except:
    print( 'Failed to load image %s' % path )
    sys.exit(1)

  img = ImageOps.invert(img)

  return np.array( list( img.getdata() ), np.complex_ ).reshape( (img.size[1],img.size[0]) )



# Handle window reshape

def reshape( newWidth, newHeight ):

  global windowWidth, windowHeight

  windowWidth  = newWidth
  windowHeight = newHeight

  glViewport( 0, 0, windowWidth, windowHeight )



# Output an image
#
# The image has complex values, so output either the magnitudes or the
# phases, according to the 'outputMagnitudes' parameter.

def outputImage( image, filename, outputMagnitudes, isFT, invert ):

  if not isFT:
    show = np.real(image)
  else:
    ak =  2 * np.real(image)
    bk = -2 * np.imag(image)
    if outputMagnitudes:
      show = np.log( 1 + np.sqrt( ak*ak + bk*bk ) ) # take the log because there are a few very large values (e.g. the DC component)
    else:
      show = np.arctan2( -1 * bk, ak )
    show = np.fft.fftshift( show ) # shift FT so that origin is in centre

  min = show.min()
  max = show.max()

  img = Image.fromarray( np.uint8( (show - min) * (255 / (max-min)) ) ).transpose( Image.FLIP_TOP_BOTTOM )

  if invert:
    img = ImageOps.invert(img) 

  img.save( filename )




# Draw text in window

def drawText( x, y, text ):

  glRasterPos( x, y )
  #for ch in text:
    #glutBitmapCharacter( GLUT_BITMAP_8_BY_13, ord(ch) )

    

# Handle window reshape


def windowReshapeCallback( window, newWidth, newHeight ):

    global windowWidth, windowHeight

    windowWidth  = newWidth
    windowHeight = newHeight


# Handle mouse click


currentButton = None
initX = 0
initY = 0
initZoom = 0
initTranslate = (0,0)

def mouseButtonCallback( window, btn, action, keyModifiers ):

  global currentButton, initX, initY, initZoom, initTranslate, translate, zoom

  x,y = glfw.get_cursor_pos( window )

  if action == glfw.PRESS:

    currentButton = btn
    initX = x
    initY = y
    initZoom = zoom
    initTranslate = translate

  elif action == glfw.RELEASE:

    currentButton = None

    if btn == glfw.MOUSE_BUTTON_LEFT and initX == x and initY == y: # Process a left click (with no dragging)

      # Find which image the click is in

      toDraw, rows, cols, maxHeight, maxWidth, scale, horizSpacing, vertSpacing = getImagesInfo()

      row = (y-vertSpacing ) / float(maxHeight+vertSpacing)
      col = (x-horizSpacing) / float(maxWidth+horizSpacing)

      if row < 0 or row-math.floor(row) > maxHeight/(maxHeight+vertSpacing):
        return

      if col < 0 or col-math.floor(col) > maxWidth/(maxWidth+horizSpacing):
        return

      # Get the image

      image = toDraw[ int(row) ][ int(col) ]

      if image is None:
        return

      # Get bounds of visible image
      #
      # Bounds are [cx-offset,cx+offset] x [cy-offset,cy+offset]
      
      height = scale * image.shape[0]
      width  = scale * image.shape[1]

      cx     = 0.5 - translate[0]/width
      cy     = 0.5 - translate[1]/height
      offset = 0.5 / zoom

      # Find pixel position within the image array

      xFraction = (col-math.floor(col)) / (maxWidth /float(maxWidth +horizSpacing))
      yFraction = (row-math.floor(row)) / (maxHeight/float(maxHeight+vertSpacing ))

      pixelX = int( image.shape[1] * ((1-xFraction)*(cx-offset) + xFraction*(cx+offset)) )
      pixelY = int( image.shape[0] * ((1-yFraction)*(cy+offset) + yFraction*(cy-offset)) )
      
      # for the FT images, move the position half up and half right,
      # since the image is displayed with that shift, while the FT array
      # stores the unshifted values.

      isFT = (int(row) == 1)

      if isFT:

        pixelX = pixelX - image.shape[1]/2
        if pixelX < 0:
          pixelX = pixelX + image.shape[1]

        pixelY = pixelY - image.shape[0]/2
        if pixelY < 0:
          pixelY = pixelY + image.shape[0]

      # Perform the operation
      #
      # No operation is implemented here, but could be (e.g. image modification at the mouse position)

      # applyOperation( image, pixelX, pixelY, isFT )  

      print( 'click at', pixelX, pixelY, '=', image[pixelY][pixelX], np.absolute(image[pixelY][pixelX]) )

      # Done



# Handle mouse motion.  We don't want to transform the image and
# redraw with each tiny mouse movement.  Instead, just record the fact
# that the mouse moved.  After events are process in
# glfw.wait_events(), check whether the mouse moved and, if so, act on
# it.

mousePositionChanged = False

def mouseMovementCallback( window, x, y ):

  global mousePositionChanged

  if currentButton is not None: # button is down
    mousePositionChanged = True



# Handle mouse dragging
#
# Zoom out/in with right button dragging up/down.
# Translate with left button dragging.


def actOnMouseMovement( window, x, y ):

  global zoom, translate

  if currentButton == glfw.MOUSE_BUTTON_RIGHT:

    # zoom

    factor = 1 # controls the zoom rate
    
    if y > initY: # zoom in
      zoom = initZoom * (1 + factor*(y-initY)/float(windowHeight))
    else: # zoom out
      zoom = initZoom / (1 + factor*(initY-y)/float(windowHeight))

  elif currentButton == glfw.MOUSE_BUTTON_LEFT:

    # translate

    translate = ( initTranslate[0] + (x-initX)/zoom, initTranslate[1] + (initY-y)/zoom )


# For an image coordinate, if it's < 0 or >= max, wrap the coorindate
# around so that it's in the range [0,max-1].  This is useful dealing
# with FT images.

def wrap( val, max ):

  if val < 0:
    return val+max
  elif val >= max:
    return val-max
  else:
    return val



# Initialize GLFW and run the main event loop

def main_interactive():

    if not glfw.init():
        print( 'Error: GLFW failed to initialize' )
        sys.exit(1)

    window = glfw.create_window( windowWidth, windowHeight, "Assignment 2", None, None )

    if not window:
        glfw.terminate()
        print( 'Error: GLFW failed to create a window' )
        sys.exit(1)

    glfw.make_context_current( window )

    glfw.swap_interval( 1 )  # redraw at most every 1 screen scan

    # Use GLUT for bitmapped characters

    #glutInit()

    # Callbacks
    
    glfw.set_key_callback( window, keyCallback )
    glfw.set_window_size_callback( window, windowReshapeCallback )
    glfw.set_mouse_button_callback( window, mouseButtonCallback )
    glfw.set_cursor_pos_callback( window, mouseMovementCallback )

    loadImage( os.path.join( imageDir, imageFilename ) )

    display( window )

    # Main event loop

    prevX, prevY = glfw.get_cursor_pos( window )

    while not glfw.window_should_close( window ):

        glfw.wait_events()

        currentX, currentY = glfw.get_cursor_pos( window )
        if currentX != prevX or currentY != prevY:
          actOnMouseMovement( window, currentX, currentY )

        display( window )

    glfw.destroy_window( window )
    glfw.terminate()



# Load initial data
#
# The command line (stored in sys.argv) could have:
#
#     main.py {image filename}

if len(sys.argv) > 1:
  imageFilename = sys.argv[1]
  imagePath = os.path.join( imageDir,  imageFilename  )

image  = loadImage( imagePath )


# If commands exist on the command line (i.e. there are more than two
# arguments), process each command, then exit.  Otherwise, go into
# interactive mode.
#
# DO NOT MODIFY THIS CODE, AS IT IS USED FOR TESTING THE ASSIGNMENT.
#
# You can use this for your own testing, if you wish.

if len(sys.argv) <= 2:

  main_interactive()

else:

  # process commands
      
  outputMagnitudes = True

  # process commands

  cmds = sys.argv[2:]

  while len(cmds) > 0:
    cmd = cmds.pop(0)
    if cmd == 'f':
      forwardFT_all()
    elif cmd == 'i':
      inverseFT_all()
    elif cmd == 'm':
      outputMagnitudes = True
    elif cmd == 'p':
      outputMagnitudes = False
    elif cmd == 'c':
      image, lines = compute()
      print( lines )
    elif cmd[0] == 'o': # image name follows in 'cmds'
      filename = cmds.pop(0)
      outputImage( resultImage, filename, False, False, True )
    else:
      print( """command '%s' not understood.
command-line arguments:
  c - compute  
  f - apply forward FT
  i - apply inverse FT
  o - output the image
  m - for output, use magnitudes (default)
  p - for output, use phases""" % cmd )
