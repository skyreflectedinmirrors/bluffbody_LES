cp -r 0.orig 0
mapFields ../RAS -sourceTime latestTime -consistent
renumberMesh -latestTime -overwrite
decomposePar
