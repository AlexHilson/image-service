import numpy as np
from vispy import app
from vispy import gloo
from vispy.io import imsave
import OpenGL.GL as gl
from scipy import misc
import os
homeDir = os.path.dirname(__file__)

def getCloudTexture(imgPath, imgWidth, imgHeight):
	'''
	Reads an image file, converts from 0-255 to 0-1, and loads into a 2D texture.
	@type imgPath: string
	@type imgWidth: number
	@type ingHeight: number
	@return: gloo.Texture2D
	'''
	cloudImage = misc.imread(imgPath)
	divisor = np.full((imgWidth, imgHeight, 3), 255.0)
	cloudScaledImage = np.divide(cloudImage, divisor).astype(np.float32)
	cloudTexture = gloo.Texture2D(cloudScaledImage)
	return cloudTexture

def getShader(shaderPath):
	'''
	Loads a glsl shader as a string.
	@type shaderPath: string
	@return: string
	'''
	shaderFile = open(shaderPath, 'rb')
	shader = shaderFile.read()
	shaderFile.close()
	return shader

def mkProgram(vShader, fShader, texture, dataShape, textureShape, tileLayout):
	'''
	Sets up a program with the given vertex and fragment shaders, and sets 
	the following shader attributes:
		dataTexture, textureShape, u_resolution, dataShape,
		nSlices, texLevels, nSlicesPerRow, maxRow, a_position
	@type vShader, fShader: string
	@type texture: gloo.Texture2D
	@type dataShape: 3-tuple
	@type textureShape: 2-tuple
	@type tileLayout: 2-tuple
	@return: gloo.Program 
	'''
	program = gloo.Program(vShader, fShader, count=4)
	program['dataTexture'] = texture
	program['textureShape'] = textureShape
	program['u_resolution'] = textureShape
	program['dataShape'] = dataShape

	nTiles = tileLayout[0] * tileLayout[1]
	program['nSlices'] = nTiles
	program['texLevels'] = nTiles * 3
	program['nSlicesPerRow'] = tileLayout[0]
	program['maxRow'] = tileLayout[1] - 1

	width = textureShape[0]
	height = textureShape[1]
	my_positions_array = np.array([ (0, 0), (0, height), (width, 0), (width, height) ])
	program['a_position'] = gloo.VertexBuffer(my_positions_array.astype(np.float32))

	return program

def setLightPosition(program, position):
	'''
	Sets the program's lightPosition attribute.
	@type program: gloo.Program
	@type position: 3-tuple
	'''
	program['lightDirection'] = position

def setResolution(program, steps, alphaScale):
	'''
	Sets the program's steps and alphaCorrection attributes.
	@type program: gloo.Program
	@type steps: int
	@type alphaScale: int
	'''
	program['steps'] = steps
	program['alphaCorrection'] = alphaScale/float(steps)

def drawShadows(inputFile='/Users/rachel/Downloads/cloud_frac_padded_623_812_70_4096_4096.png',
				outputFile='/Users/rachel/Downloads/newshadow.png',
				lightPosition=(20, 0, 0),
				dataShape=(623, 812, 70),
				textureShape=(4096, 4096),
				tileLayout=(6,5),
				steps=81,
				alphaScale=2):
	'''
	Given a tiled data PNG file and a light position, computes the shadows
	on the data and writes them to a second PNG.
	@param inputFile: path to the input PNG
	@type inputFile: string
	@param outputFile: path to write out the results
	@type outputFile: string
	@param lightPosition: position of the point light
	@type lightPosition: 3-tuple
	@param dataShape: 3D shape of the data field
	@type dataShape: 3-tuple
	@param textureShape: shape of the input image
	@type textureShape: 2-tuple
	@param tileLayout: (cols, rows) arrangement of tiles in the input PNG
	@type tileLayout: 2-tuple
	@param steps: how many steps to take through the data in calculations
	@type steps: int
	@param alphaScale: factor to scale the light absorption
	@type alphaScale: number
	'''
	
	width = textureShape[0]
	height = textureShape[1]

	c = app.Canvas(show=False, size=(width, height))

	cloudTex = getCloudTexture(inputFile, width, height)
	vertexPath = os.path.join(homeDir, 'shadow_vertex.glsl')
	fragmentPath = os.path.join(homeDir, 'shadow_frag.glsl')
	vertex = getShader(vertexPath)
	fragment = getShader(fragmentPath)

	program = mkProgram(vertex, fragment, cloudTex, dataShape=dataShape, textureShape=textureShape, tileLayout=tileLayout)
	setLightPosition(program, lightPosition)
	setResolution(program, steps, alphaScale)

	@c.connect
	def on_draw(event):
	    gloo.clear((1,1,1,1))
	    program.draw(gl.GL_TRIANGLE_STRIP)
	    im = gloo.util._screenshot((0, 0, c.size[0], c.size[1]))
	    imsave(outputFile, im)
	    c.close()

	app.run()