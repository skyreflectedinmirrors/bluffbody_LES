cp -r 0.orig 0
mapFieldsPar ../RAS -fields "(U T p)" -sourceTime latestTime -consistent -mapMethod mapNearest
renumberMesh -latestTime -overwrite
decomposePar
