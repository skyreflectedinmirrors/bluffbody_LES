cp -r 0.orig 0
mapFields ../RAS -consistent
decomposePar
renumberMesh -latestTime -overwrite
