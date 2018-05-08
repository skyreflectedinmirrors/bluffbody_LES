mkdir -p 0 && blockMesh && cp -rv 0.orig/* 0 && mapFields ../potential && renumberMesh -latestTime -overwrite && decomposePar
