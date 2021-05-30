
singleton Material(roadmarkings1)
{
    mapTo = "unmapped_mat";
    diffuseMap[0] = "roadmarkings1.dds";
    materialTag0 = "decal";
    materialTag1 = "road";
    materialTag2 = "beamng";
    translucent = "1";
    translucentZWrite = "1";
    specularPower[0] = "1";
    useAnisotropic[0] = "1";
    annotation = "DRIVING_INSTRUCTIONS";
    annotationMap = "roadmarkings1_annotation.png";
};

singleton Material(graffiti)
{
    mapTo = "unmapped_mat";
    diffuseMap[0] = "decals_graffiti.dds";
    materialTag0 = "decal";
    materialTag1 = "road";
    materialTag2 = "beamng";
    translucent = "1";
    translucentZWrite = "1";
    specularPower[0] = "1";
    useAnisotropic[0] = "1";
};

singleton Material(damage)
{
    mapTo = "damage";
    diffuseMap[0] = "decals_damage.dds";
    materialTag0 = "decal";
    materialTag1 = "road";
    materialTag2 = "beamng";
    translucent = "1";
    translucentZWrite = "1";
    specularPower[0] = "1";
    useAnisotropic[0] = "1";
};
