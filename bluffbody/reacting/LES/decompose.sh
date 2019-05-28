rm -r 0 && rm -r processor*
mkdir -p 0 && cp -rv 0.orig/* 0
blockMesh
mapFields ../LES_accelerint -sourceTime $1 -consistent
renumberMesh -latestTime -overwrite
decomposePar
