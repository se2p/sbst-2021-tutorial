// This is the default save location for any Decal datablocks created in the
// Decal Editor (this script is executed from onServerCreated())


datablock DecalData(NewDecalData)
{
    Material = "WarningMaterial";
};

datablock DecalData(decal_roadmarkings1)
{
    Material = "roadmarkings1";
    textureCoordCount = "15";
    size = "1";
    textureCoords[0] = "0 0 0.25 0.25";
    textureCoords[1] = "0.25 0 0.25 0.25";
    fadeStartPixelSize = "10";
    fadeEndPixelSize = "5";
   frame = "15";
   texRows = "4";
   texCols = "4";
   textureCoords[2] = "0.5 0 0.25 0.25";
   textureCoords[3] = "0.75 0 0.25 0.25";
   textureCoords[4] = "0 0.25 0.25 0.25";
   textureCoords[5] = "0.25 0.25 0.25 0.25";
   textureCoords[6] = "0.5 0.25 0.25 0.25";
   textureCoords[7] = "0.75 0.25 0.25 0.25";
   textureCoords[8] = "0 0.5 0.25 0.25";
   textureCoords[9] = "0.25 0.5 0.25 0.25";
   textureCoords[10] = "0.5 0.5 0.25 0.25";
   textureCoords[11] = "0.75 0.5 0.25 0.25";
   textureCoords[12] = "0 0.75 0.25 0.25";
   textureCoords[13] = "0.25 0.75 0.25 0.25";
   textureCoords[14] = "0.5 0.75 0.25 0.25";
   textureCoords[15] = "0.75 0.75 0.25 0.25";
   renderPriority = "9";
};

datablock DecalData(decal_graffiti)
{
    Material = "graffiti";
    textureCoordCount = "15";
    size = "5";
    textureCoords[0] = "0 0 0.25 0.25";
    textureCoords[1] = "0.25 0 0.25 0.25";
    fadeStartPixelSize = "50";
    fadeEndPixelSize = "60";
   frame = "1";
   texRows = "4";
   texCols = "4";
   textureCoords[2] = "0.5 0 0.25 0.25";
   textureCoords[3] = "0.75 0 0.25 0.25";
   textureCoords[4] = "0 0.25 0.25 0.25";
   textureCoords[5] = "0.25 0.25 0.25 0.25";
   textureCoords[6] = "0.5 0.25 0.25 0.25";
   textureCoords[7] = "0.75 0.25 0.25 0.25";
   textureCoords[8] = "0 0.5 0.25 0.25";
   textureCoords[9] = "0.25 0.5 0.25 0.25";
   textureCoords[10] = "0.5 0.5 0.25 0.25";
   textureCoords[11] = "0.75 0.5 0.25 0.25";
   textureCoords[12] = "0 0.75 0.25 0.25";
   textureCoords[13] = "0.25 0.75 0.25 0.25";
   textureCoords[14] = "0.5 0.75 0.25 0.25";
   textureCoords[15] = "0.75 0.75 0.25 0.25";
   renderPriority = "9";
   randomize = "1";
};

datablock DecalData(decal_damage)
{
   size = "6";
   Material = "damage";
   fadeStartPixelSize = "2";
   fadeEndPixelSize = "60";
   renderPriority = "8";
   frame = "3";
   randomize = "1";
   textureCoordCount = "15";
   texRows = "4";
   texCols = "4";
   textureCoords[1] = "0.25 0 0.25 0.25";
   textureCoords[2] = "0.5 0 0.25 0.25";
   textureCoords[3] = "0.75 0 0.25 0.25";
   textureCoords[4] = "0 0.25 0.25 0.25";
   textureCoords[5] = "0.25 0.25 0.25 0.25";
   textureCoords[6] = "0.5 0.25 0.25 0.25";
   textureCoords[7] = "0.75 0.25 0.25 0.25";
   textureCoords[8] = "0 0.5 0.25 0.25";
   textureCoords[9] = "0.25 0.5 0.25 0.25";
   textureCoords[10] = "0.5 0.5 0.25 0.25";
   textureCoords[11] = "0.75 0.5 0.25 0.25";
   textureCoords[12] = "0 0.75 0.25 0.25";
   textureCoords[13] = "0.25 0.75 0.25 0.25";
   textureCoords[14] = "0.5 0.75 0.25 0.25";
   textureCoords[15] = "0.75 0.75 0.25 0.25";
   textureCoords[0] = "0 0 0.25 0.25";
};
