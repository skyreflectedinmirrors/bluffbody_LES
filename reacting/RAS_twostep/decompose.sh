rm -r 0
mkdir -p 0 && cp -rv 0.orig/* 0
blockMesh
mapFields ../XiFoam -sourceTime 'latestTime' -parallelSource
renumberMesh -latestTime -overwrite
decomposePar
