import numpy as np
from vispy import app
from vispy import gloo
from vispy.io import imsave
import OpenGL.GL as gl
from scipy import misc
import os
homeDir = os.path.dirname(__file__)


def makeTexture(dataArray, imgWidth, imgHeight):
    '''
    Reads an image file, converts from 0-255 to 0-1, and loads into a 2D texture.
    Args:
        * dataArray (str)
        * imgWidth (int)
        * ingHeight (int)
    
    returns gloo.Texture2D

    '''
    scaledData = dataArray / dataArray.max()
    cloudTexture = gloo.Texture2D(scaledData.astype(np.float32))

    return cloudTexture


def getShader(shaderPath):
    '''
    Loads a glsl shader as a string.

    Args:
        * shaderPath (str)
    
    returns string

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
    
    Args:
        * vShader (str)
        * fShader (str)
        * texture (gloo.Texture2D)
        * dataShape (3-tuple)
        * textureShape (2-tuple)
        * tileLayout (2-tuple)

    returns gloo.Program

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
    
    Args:
        * program (gloo.Program)
        * position (3-tuple)

    '''
    program['lightDirection'] = position


def setResolution(program, steps, alphaScale):
    '''
    Sets the program's steps and alphaCorrection attributes.

    Args:
        * program (gloo.Program)
        * steps (int)
        * alphaScale (int)
    '''
    program['steps'] = steps
    program['alphaCorrection'] = alphaScale/float(steps)


def procShadows(dataArray,
                lightPosition=(20, 0, 0),
                dataShape=(623, 812, 70),
                textureShape=(4096, 4096),
                tileLayout=(6,5),
                steps=81,
                alphaScale=2):
    '''
    Given a tiled data PNG file and a light position, computes the shadows
    on the data and writes them to a second PNG.

    Args:
        * dataArray (array): data for which to calculate shadows
        * lightPosition (3-tuple): position of the point light
        * dataShape (3-tuple): 3D shape of the data field
        * textureShape (3-tuple): shape of the input image
        * tileLayout (2-tuple): (cols, rows) arrangement of tiles in the input PNG
        * steps (int): how many steps to take through the data in calculations
        * alphaScale (int): factor to scale the light absorption
        
    '''
    
    width = textureShape[0]
    height = textureShape[1]

    c = app.Canvas(show=False, size=(width, height))

    cloudTex = getCloudTexture(dataArray, width, height)
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
        shadowsArray = gloo.util._screenshot((0, 0, c.size[0], c.size[1]))
        c.close()

        return shadowsArray

    app.run()


if __name__ == "__main__":
    pass