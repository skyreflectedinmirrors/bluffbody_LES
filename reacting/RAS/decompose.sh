rm -r 0
mkdir -p 0 && cp -rv 0.orig/* 0
blockMesh
mapFields ../RAS_twostep -sourceTime latestTime -consistent
setFields
renumberMesh -latestTime -overwrite
decomposePar
