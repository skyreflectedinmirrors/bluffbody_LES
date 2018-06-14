rm -r 0
mkdir -p 0 && cp -rv 0.orig/* 0
blockMesh
mapFields ../../non-reacting/LES -sourceTime 'latestTime' -parallelSource
setFields
renumberMesh -latestTime -overwrite
decomposePar
