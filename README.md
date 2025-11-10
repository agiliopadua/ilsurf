# Simulation of ILs at interfaces

## Create graphene planes from crystal structure

Download a CIF file for graphite from the Crystallography Open Database: `9011577.cif`

Using `Vesta`, in `Boundary`, set ranges of fractional coordinates: x(max) = 26.4, y(max) = 19.9, z(max) = 1.

Add cutoff planes:

- (2 -1 0), distance from origin 33 x d
- (-2 1 0), distance from origin 0.1 x d

Remove atoms with $x < 0$, $y < 0$, and those to the right with $x > 40.7$ (using the pointer selection). Verify that the boundaries are matching and export to `xyz` format. Check that you have 680 atoms per plane. Change z(max) to control the number of planes.


## Simulation box with periodic graphene planes

Copy the `.xyz` file with the coordinates of the graphene planes and replace all `C` atom names with `CG`:

        sed 's/C /CG/' < planes.xyz > graph.xyz

Two planes of graphene of dimensions 41.888 x 42.678 A, with 1360 atoms.

        cd mols
        fftool 1 graph.xyz -b 41.888,42.678,40
        packmol < gr_pack.inp
        fftool 1 graph.xyz -b 41.888,42.678,40 -p xy -xml -a

With the planes stitched across box boundaries we expect 1.5 * 1360 = 2040 bonds.

Test just the graphene:

        cp field.xml config.pdb ../graph
        cd ../graph
        ./omm.py

Check energies and density to see if box size adapts.

        vmd -e ../mols/pbc.vmd config.pdb traj.dcd


## Add ionic liquid

Put 200 ion pairs above the graphene planes

        cd mols
        fftool 1 graph.xyz 200 c2c1im.zmat 200 BF4.zmat -b 41.888,42.678,100
        packmol < gr_il_pack.inp
        fftool 1 graph.xyz 200 c2c1im.zmat 200 BF4.zmat -b 41.888,42.678,100 -p xy -xml -a

        cp field.xml condfig.pdb ../gr_c2mim_bf4
        cd ../gr_c2mim_bf4
        ./omm.py

        vmd -e ../mols/pbc.vmd config.pdb traj.dcd

Repeat with c8c1im. Edit `gr_il_pack.inp` to allow more space for the larger cation, or use less ion pairs.
