rm -r 0
mkdir -p 0 && cp -rv 0.orig/* 0 && mapFields ../RAS_laminar -consistent -sourceTime 'latestTime' -parallelSource && renumberMesh -latestTime -overwrite && decomposePar
