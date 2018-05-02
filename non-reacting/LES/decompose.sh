cp -r 0.orig 0
mapFields ../RAS -fields "(U T p)" -sourceTime latestTime -consistent
renumberMesh -latestTime -overwrite
decomposePar
