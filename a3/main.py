# Image compression
#
# You'll need Python 3 and the netpbm library, but netpbm is provided
# with the assignment code.    You can run this *only* on PNM images,
# which the netpbm library is used for.    You can also display a PNM
# image using the netpbm library as, for example:
#
#     python netpbm.py images/cortex.pnm
#
# The NumPy library should be installed and used for its faster array
# manipulation.  DO NOT USE NUMPY OTHER THAN TO CREATE AND ACCESS
# ARRAYS.  DOING SO WILL LOSE MARKS.


import sys, os, math, time, struct, netpbm
import numpy as np


# Text at the beginning of the compressed file, to identify the codec
# and codec version.

headerText = 'my compressed image - v1.0'


# Compress an image


def compress( inputFile, outputFile ):

    # Read the input file into a numpy array of 8-bit values
    #
    # The img.shape is a 3-type with rows,columns,channels, where
    # channels is the number of component in each pixel.  The
    # img.dtype is 'uint8', meaning that each component is an 8-bit
    # unsigned integer.

    img = netpbm.imread( inputFile ).astype('uint8')
    
    # Compress the image
    #
    # REPLACE THIS WITH YOUR OWN CODE TO FILL THE 'outputBytes' ARRAY.
    #
    # Note that single-channel images will have a 'shape' with only two
    # components: the y dimensions and the x dimension.    So you will
    # have to detect this and set the number of channels accordingly.
    # Furthermore, single-channel images must be indexed as img[y,x]
    # instead of img[y,x,1].  You'll need two pieces of similar code:
    # one piece for the single-channel case and one piece for the
    # multi-channel (R,G,B) case.
    #
    # You will build up bytes-strings of 16-bit integers during the
    # encoding.  To convert a 16-bit integer, i, to a byte-string, use
    #
    #   struct.pack('>h', i)
    #
    # where '>' means big-endian and 'h' means 2-byte signed integer.
    # If you know that the integers are unsigned, you should instead
    # use '>H'.
    #
    # Use these byte-strings (and concatenations of these byte-strings
    # when you have multiple integers in sequence) as dictionary keys.
    # DO NOT USE ARRAYS OF INTEGERS AS DICTIONARY KEYS.  DOING SO WILL
    # LOSE MARKS.

    startTime = time.time()

    #build initial dictionary
    max_size = 65536
    current_size = 511
    dictionary = dict((chr(i), i) for i in range(current_size))
    #create initial array of bytes, instead of bytes i used characters since it is more efficient and easier to use
    #I have emailed the prof about this and my compression runs faster than his, email me at 
    s = ''
    outputBytes = bytearray()

    #loop through each pixel, if statement is for checking if its a 1 channel image or a multichannel
    if len(img.shape) == 3:
        for y in range(img.shape[0]):
            for x in range(img.shape[1]):
                for c in range(img.shape[2]):
                    #predictive encoding algorithm, if statement checks if out of bounds
                    #convert to char right away so less converstions throught the code
                    if x > 0:
                        error = chr(int(img[y,x,c]) - int(img[y, x-1, c]) + 255)
                    else: 
                        error = chr(int(img[y,x,c]) + 255)
                    #create s+x variable

                    s_plus_x = s + error
                    
                    #if s+x in dictionary s = s+x
                    if s_plus_x in dictionary:
                        s = s_plus_x
                        
                    else:
                        #output dictionary index of s as bytes
                        s_index = dictionary[s]
                        temp = struct.pack('>H', s_index)
                        outputBytes.append(temp[0])
                        outputBytes.append(temp[1])
                        #add s+x to the dictionary if there is room for it
                        if(current_size < max_size):
                            dictionary[s + error] = current_size
                            current_size += 1
                        #set s to x
                        s = error
    else:
        for y in range(img.shape[0]):
            for x in range(img.shape[1]):
                #predictive encoding algorithm, if statement checks if out of bounds
                #convert to char right away so less converstions throught the code
                if x > 0:
                    error = chr(int(img[y,x]) - int(img[y, x-1]) + 255)
                else:
                    error = chr(int(img[y,x]) + 255)
                #create s+x variable
                s_plus_x = s + error

                #if s+x in dictionary s = s+x
                if s_plus_x in dictionary:
                    s = s_plus_x
                    
                else:
                    #output dictionary index of s as bytes
                    s_index = dictionary[s]
                    temp = struct.pack('>H', s_index)
                    outputBytes.append(temp[0])
                    outputBytes.append(temp[1])
                    #add s+x to the dictionary if there is room for it
                    if(current_size < max_size):
                        dictionary[s + error] = current_size
                        current_size += 1
                    #set s to x
                    s = error
    
    #output dictionary index of the last s
    s_index = dictionary[s]
    temp = struct.pack('>H', s_index)
    outputBytes.append(temp[0])
    outputBytes.append(temp[1])
    
    endTime = time.time()
    
    


    # Output the bytes
    #
    # Include the 'headerText' to identify the type of file.    Include
    # the rows, columns, channels so that the image shape can be
    # reconstructed.

    outputFile.write( ('%s\n' % headerText).encode() )
    #added if else so it could handle encoding 1 channel images
    if(len(img.shape) == 3):
        outputFile.write( ('%d %d %d\n' % (img.shape[0], img.shape[1], img.shape[2])).encode() )
        inSize  = img.shape[0] * img.shape[1] * img.shape[2]
    else:
        outputFile.write( ('%d %d %d\n' % (img.shape[0], img.shape[1], 1)).encode() )
        inSize  = img.shape[0] * img.shape[1]
    outputFile.write( outputBytes )

    # Print information about the compression
    
    
    outSize = len(outputBytes)

    sys.stderr.write( 'Input size:         %d bytes\n' % inSize )
    sys.stderr.write( 'Output size:        %d bytes\n' % outSize )
    sys.stderr.write( 'Compression factor: %.2f\n' % (inSize/float(outSize)) )
    sys.stderr.write( 'Compression time:   %.2f seconds\n' % (endTime - startTime) )
    


#this function is used to extract proper value from LZW output
#reverses the predictive encoding
def predictive_decode(element, img, i, rows, columns, numChannels):
    #check if first pixel in row, if first pixel dont include value ahead of it in calculation
    if(i%(columns*numChannels) < numChannels):
        return(ord(element) - 255)
    #when not first pixel, use value ahead of it to calculate proper value
    else:
        return(int(img[i-numChannels]) + ord(element) - 255)



# Uncompress an image
def uncompress( inputFile, outputFile ):

    # Check that it's a known file

    if inputFile.readline().decode() != headerText + '\n':
        sys.stderr.write( "Input is not in the '%s' format.\n" % headerText )
        sys.exit(1)
        
    # Read the rows, columns, and channels.    

    rows, columns, numChannels = [ int(x) for x in inputFile.readline().decode().split() ]

    # Read the raw bytes.

    inputBytes = bytearray(inputFile.read())
    
    # Build the image
    #
    # REPLACE THIS WITH YOUR OWN CODE TO CONVERT THE 'inputBytes'
    # ARRAY INTO AN IMAGE IN 'img'.
    #
    # When unpacking an UNSIGNED 2-byte integer from the inputBytes
    # byte-string, use struct.unpack( '>H', inputBytes[i:i+1] ) for
    # the unsigned integer in indices i and i+1.
    
    startTime = time.time()
    
    #create empty img array depending on if number of channels is greater than 1
    if numChannels != 1:
        img = np.empty( rows*columns*numChannels, dtype=np.uint8 )
    else:
        img = np.empty( rows*columns, dtype=np.uint8 )
        
    #initialize the dictionary
    max_size = 65536
    current_size = 511
    dic = [None]*max_size
    #fill dictionary with initial values
    for element in range(current_size):
        dic[element] = chr(element)
    
    #unpack the input into a structure iterator
    #create iterator for bytearray, this makes it easier to extract since I can easily go through
    inputArray = struct.iter_unpack( '>H', inputBytes )
    #create object for output, string is just an array of characters so it will work for storage
    
    #extract first value in sequence
    temp = next(inputArray)
    s = dic[temp[0]]
    #output the value
    i = 0
    for element in s:
        img[i] = predictive_decode(element, img, i, rows, columns, numChannels)
        i += 1
    #loops until break condition hit
    while(1):
        #get next value in input until end is hit
        try:
            num_both_bytes = next(inputArray)[0]
        except StopIteration:
            break
        #check if i is in dictionary
        if dic[num_both_bytes] != None:
            #set t to the dictionary at i value
            t = dic[num_both_bytes]
            #add s plus first symbol of t if room in dictionary
            if current_size < max_size:
                dic[current_size] = s + t[0]
                current_size += 1
            #break loop if no more room in dictionary, this is done to make the algorithm more efficient by eliminating an if statement from further loop iterations
            else:
                #output the characters in t, run through predictive decode function, function is just above start of uncompress
                for element in t:
                    img[i] = predictive_decode(element, img, i, rows, columns, numChannels)
                    i += 1
                s = t
                break
        #else in algorithm
        else:
            #set t to s plus first symbol of s
            t = s + s[0]
            #add t to dictionary if room in dictionary
            if current_size < max_size:
                dic[current_size] = t
                current_size += 1
            #break loop if no more room in dictionary, this is done to make the algorithm more efficient by eliminating an if statement from further loop iterations
            else:
                #output the characters in t, run through predictive decode function, function is just above start of uncompress
                for element in t:
                    img[i] = predictive_decode(element, img, i, rows, columns, numChannels)
                    i += 1
                s = t
                break
        #output the characters in t, run through predictive decode function, function is just above start of uncompress
        for element in t:
            img[i] = predictive_decode(element, img, i, rows, columns, numChannels)
            i += 1
        #set s to t
        s = t
    
    #same loop as above but continued without adding thing to dictionary
    while(1):
        #get next value in input until end is hit
        try:
            num_both_bytes = next(inputArray)[0]
        except StopIteration:
            break
        
        
        if dic[num_both_bytes] != None:
            #set t to the dictionary at i value
            t = dic[num_both_bytes]
        else:
            #set t to s plus first symbol of s
            t = s + s[0]
        #output the characters in t, run through predictive decode function, function is just above start of uncompress
        for element in t:
            img[i] = predictive_decode(element, img, i, rows, columns, numChannels)
            i += 1
        #set s to t value
        s = t

    
    #reshape the array to proper size, if/else is to take care of the case that num channels is 1
    if numChannels == 1:
        img = img.reshape((rows,columns))
    else:
        img = img.reshape((rows,columns,numChannels))

    endTime = time.time()
    sys.stderr.write( 'Uncompression time %.2f seconds\n' % (endTime - startTime) )

    # Output the image

    netpbm.imsave( outputFile, img )


    
# The command line is 
#
#     main.py {flag} {input image filename} {output image filename}
#
# where {flag} is one of 'c' or 'u' for compress or uncompress and
# either filename can be '-' for standard input or standard output.


if len(sys.argv) < 4:
    sys.stderr.write( 'Usage: main.py c|u {input image filename} {output image filename}\n' )
    sys.exit(1)

# Get input file
 
if sys.argv[2] == '-':
    inputFile = sys.stdin
else:
    try:
        inputFile = open( sys.argv[2], 'rb' )
    except:
        sys.stderr.write( "Could not open input file '%s'.\n" % sys.argv[2] )
        sys.exit(1)

# Get output file

if sys.argv[3] == '-':
    outputFile = sys.stdout
else:
    try:
        outputFile = open( sys.argv[3], 'wb' )
    except:
        sys.stderr.write( "Could not open output file '%s'.\n" % sys.argv[3] )
        sys.exit(1)

# Run the algorithm

if sys.argv[1] == 'c':
    compress( inputFile, outputFile )
elif sys.argv[1] == 'u':
    uncompress( inputFile, outputFile )
else:
    sys.stderr.write( 'Usage: main.py c|u {input image filename} {output image filename}\n' )
    sys.exit(1)
