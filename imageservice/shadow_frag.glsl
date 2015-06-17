precision mediump float;
// our texture
uniform sampler2D dataTexture;
// the texCoords passed in from the vertex shader.
varying vec2 v_texCoord;
uniform vec3 lightDirection;
uniform vec3 dataShape;
uniform int nSlices;
uniform int nSlicesPerRow;
uniform int maxRow;
uniform float alphaCorrection;
uniform vec2 textureShape;
uniform float texLevels;
uniform float steps;
uniform float ambient;

float sliceW = dataShape.x;
float sliceH = dataShape.y;

vec3 getDatumColor(float datum) {
    vec3 color = vec3(1, 1, 0);
    return color;
}
float getDatumAlpha(float datum) {
    return datum * alphaCorrection;
}
vec3 mapTo2D(in vec3 p, float sliceW, float sliceH, int nSlicesPerRow, int nSlices){
    float zLevel = floor(p.z * texLevels);
    float zIndex = floor(zLevel / float(nSlices));
    float sliceIndex = (zLevel - (zIndex * float(nSlices)));
    float oSliceRow = floor(sliceIndex / float(nSlicesPerRow));
    //Rows are now in the opposite order
    float sliceRow = float(maxRow) - oSliceRow;
    float sliceCol = sliceIndex - float(nSlicesPerRow) * oSliceRow;
    
    vec2 pxy = (p.xy + vec2(sliceCol, sliceRow)) * vec2(sliceW, sliceH);
    return vec3(pxy, zIndex);
}
float sample3DTexture(sampler2D slices, vec3 p, float sliceW, float sliceH, int nSlicesPerRow, int nSlices, float bias){
    if(any(greaterThan(p, vec3(1.0))) || any(lessThan(p, vec3(0.0))))
       return 0.0;
    vec3 position = mapTo2D(p, sliceW, sliceH, nSlicesPerRow, nSlices);
    float zTile = position.z;
    vec4 datumRGB = texture2D(slices, position.xy / textureShape, bias);
    float datum;
    if (zTile == 0.0){
        datum = datumRGB.r;
    }else if (zTile == 1.0){
        datum = datumRGB.g;
    }else if (zTile == 2.0){
        datum = datumRGB.b;
    }
    return datum;
}
float sample3DTexture(sampler2D slices, vec3 p, float sliceW, float sliceH, int nSlicesPerRow, int nSlices){
    return sample3DTexture(slices, p, sliceW, sliceH, nSlicesPerRow, nSlices, 0.0);
}
vec4 getRGBAfromDataTex(sampler2D tex, vec3 pos, vec3 dataShape, vec2 texShape){
    // pos.xyz = clamp(pos.xyz, 0.01,0.99);
    //float datum = sampleAs3DTexture(tex, pos, dataShape, texShape);
    float datum = sample3DTexture(tex, pos, sliceW, sliceH, nSlicesPerRow, nSlices);
    vec3 color = getDatumColor(datum);
    float alpha = getDatumAlpha(datum);
    return vec4(color.xyz, alpha);
}
float getPathRGBA(vec3 startPos, vec3 dir, float steps, sampler2D tex){
    /* Calculates the total RGBA values of a given path through a texture */
    //The direction from the front position to back position.
    //vec3 dir = endPos - startPos;
    //vec3 dir = vec3(0.0,0.0,1.0);

    float rayLength = length(dir);

    //Calculate how long to increment in each step.
    float delta = 1.0 / steps;
    //The increment in each direction for each step.
    vec3 deltaDirection = normalize(dir) * delta;
    float deltaDirectionLength = length(deltaDirection);
    vec3 currentPosition = startPos;

    //The alpha value accumulated so far.
    float accumulatedAlpha = 0.0;

    //How long has the ray travelled so far.
    float accumulatedLength = 0.0;

    //vec4 dataSample;
    vec4 dataSample;
    float alphaSample;
    //Perform the ray marching iterations
    for(int i = 0; i < int(steps); i++){
        //Get the voxel intensity value from the 3D texture.    
        dataSample = getRGBAfromDataTex(dataTexture, currentPosition, dataShape, textureShape);
        //Store the alpha accumulated so far.
        accumulatedAlpha += (1.0 - accumulatedAlpha) * dataSample.a;
    
        //Advance the ray.
        currentPosition += deltaDirection;
        accumulatedLength += deltaDirectionLength;
                  
        //If the length traversed is more than the ray length, or if the alpha accumulated reaches 1.0 then exit.
        if(accumulatedLength >= rayLength || accumulatedAlpha >= (1.0 - ambient) ){
            break;
        }
    }
    return min(accumulatedAlpha, 1.0);
}
vec3 mapTo3D(vec3 pos, float sliceW, float sliceH, int nSlicesPerRow, int nSlices) {
	int sliceCol = int(floor(pos.x / sliceW));
	int sliceRow = int(floor(pos.y / sliceH));
    //Fix to put rows in the right order
    int sliceIndex = (((maxRow - sliceRow) * nSlicesPerRow) + (sliceCol));
	vec2 pxy = (pos.xy / vec2(sliceW, sliceH)) - vec2(sliceCol, sliceRow);
	//pos.z in {0,1,2}
	int z = ((int(pos.z) * nSlices) + sliceIndex);
	float pz = float(z)/texLevels;
	return vec3(pxy, pz);
}
void main() {
   // Look up a color from the texture.
   vec4 inPixel = texture2D(dataTexture, v_texCoord);
   vec3 rInCoord = vec3(v_texCoord*textureShape, 0.0);
   vec3 gInCoord = vec3(v_texCoord*textureShape, 1.0);
   vec3 bInCoord = vec3(v_texCoord*textureShape, 2.0);
   vec3 rPoint = mapTo3D(rInCoord, sliceW, sliceH, nSlicesPerRow, nSlices);
   vec3 bPoint = mapTo3D(bInCoord, sliceW, sliceH, nSlicesPerRow, nSlices);
   vec3 gPoint = mapTo3D(gInCoord, sliceW, sliceH, nSlicesPerRow, nSlices);
   float rOut = getPathRGBA(rPoint, lightDirection, steps, dataTexture);
   float bOut = getPathRGBA(bPoint, lightDirection, steps, dataTexture);
   float gOut = getPathRGBA(gPoint, lightDirection, steps, dataTexture);
   vec3 absorbed = vec3(rOut, gOut, bOut);
   vec3 light = vec3(1.0) - absorbed;
   gl_FragColor = vec4(absorbed, 1.0);
   //gl_FragColor = vec4(v_texCoord, 0.0 ,1.0);
}