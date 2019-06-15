rm -r 0
mkdir -p 0 && cp -rv 0.orig/* 0
blockMesh
mapFields ../../LES_accelerint_coarse/skeletal -sourceTime $1 -consistent
renumberMesh -latestTime -overwrite
decomposePar
