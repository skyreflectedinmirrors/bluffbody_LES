potentialFoam -writePhi -writep
echo "Converting to mass flux"
convertPhi -rhoRef `grep -r rho 0.orig/initialValues | sed -e 's/.*[^0-9]\([0-9]\+\)\.\([0-9]\+\)[^0-9]*$/\1\.\2/'`
mv -v 0/rhop 0/p
# don't map pressure
rm 0/p
mv -v 0/rhophi 0/phi
