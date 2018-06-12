rm -r 0
mkdir -p 0 && cp -rv 0.orig/* 0
blockMesh
mapFields ../potential
setFields
renumberMesh -latestTime -overwrite
decomposePar
