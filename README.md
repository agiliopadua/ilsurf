# Simulation of ILs at interfaces

## Requirements

- [clandp](https://github.com/paduagroup/clandp), force field for ionic liquids
- [fftool](https://github.com/paduagroup/fftool), builds initial configurations and force field for a system
- Packmol, packs molecules in a box
- VMD, trajectory visualizer
- VESTA, visualizer and editor of crystallographic files
- OpenMM, molecular dynamics code

## Create graphene planes from crystal structure

Download a CIF file for graphite from the [Crystallography Open Database](https://www.crystallography.net/): 9011577.cif

Although the unit cell corresponds to an hexagonal lattice, we will create an orthorhombic (all angles 90°) simulation box.

Using VESTA, under \<Edit\>\<Bonds\> choose each bond type on the table (there is just one type for graphite) and tick \<Do not search atoms beyond the boundary\>, then \<Apply\>.

Click \<Boundary...\> and set ranges of fractional coordinates: x(max) = 26.4, y(max) = 19.9, z(max) = 1.

Add cutoff planes:

- (2 -1 0), distance from origin 33 x d
- (-2 1 0), distance from origin 0.1 x d

Verify that the edges of the graphene planes are matching, with no duplicate atoms (only the bonds across box boundaries should be missing).

Q. Count the number of unit calls along each perpendicular direction.

Check that you have 680 atoms per plane. You can choose z(max) to control the number of planes. For the following work we will use 4 planes, so set z(max) accordingly.

Then \<Export Data...\> to XYZ format (do not save hidden atoms).

## Simulation box with periodic graphene planes

In the definition of the atom types within the force field (`nanocarbon.ff`), graphite C atoms are labelled type CG.

Copy the `.xyz` file with the coordinates of the graphene planes and replace all `C` atom names with `CG`:

    sed 's/C /CG/' < graph-4.xyz > graph.xyz

Edit the `graph.xyz` file and add the force field file to the second line, after the name of the molecule:

    2720
    graphite nanocarbon.ff
    CG   0.000000    0.000000    1.677750
    [...]

Build the input files for OpenMM with the graphene planes of dimensions 41.888 x 42.678 Å (Q. Find the origin of these lengths); specify periodic bonds on the x and y directions:

    cd mols
    fftool 1 graph.xyz -b 41.888,42.678,50 -p xy


The `gr_pack.inp` file instructs Packmol to place the structure fixed at the origin:

    packmol < gr_pack.inp

Create the input files for OpenMM:

    fftool 1 graph.xyz -b 41.888,42.678,50 -p xy -xml -a

With the planes stitched across box boundaries we expect 1.5 * 2720 = 4080 bonds.

Test a short run with just the graphene planes:

    mv field.xml config.pdb ../graph
    cd ../graph
    ./omm.py

Check energies and density to see if the box size adapts.

    vmd -e ../mols/graph.vmd config.pdb traj.dcd


## Add ionic liquid

Put 300 ion pairs above the graphene planes:

    cd mols
    fftool 1 graph.xyz 300 c2c1im.zmat 300 BF4.zmat -b 41.888,42.678,100
    packmol < gr_il_pack.inp
    vmd simbox.xyz

    fftool 1 graph.xyz 300 c2c1im.zmat 300 BF4.zmat -b 41.888,42.678,100 -p xy -xml -a

Run a short test trajectory to make sure the system is ok:

    mv field.xml condfig.pdb ../c2mim_bf4_gr
    cd ../c2mim_bf4_gr
    ./omm-test.py

    vmd -e ../mols/graph.vmd config.pdb traj.dcd

Then run an equilibration of 1 ns at 323 K; visualize it using vmd;
check values of energy to see if the system is well equilibrated; run a trajectory from its last configuration for 4 ns saving a snapshot every 1000 steps (4000 configurations).

Repeat with c8c1im. Edit `gr_il_pack.inp` to allow more space for the larger cation, or use less ion pairs in order to have similar numbers of atoms for the two ionic liquids.


## Silica surface

Open the file `POSCAR-SiO2-hydr` with VESTA. In \<Edit\>\<Bonds\>, for each bond type, select not to search atoms beyond the boundary.

Study the unit cell (lengths, angles, composition). It has 36 atoms and 44 bonds (check the types of bonds and angles and compare with the force field in `silica.ff`). This is important information to verify that bonds across periodic boundaries are correctly accounted for.

In Boundary set a 8 x 8 x 1 supercell and export to XYZ format. (You can start with a smaller supercell and attempt a larger one when more familiar with the system.)

Edit the .xyz file to set the force field file (`silica.ff`) as the second token in the second line. Change all H atom names to HO. Identify the O atoms near the surface (by their z values) and set their types to OH. Check that the numbers are identical:

    grep HO silica-881.xyz | wc -l
    grep OH silica-881.xyz | wc -l

Use fftool to prepare a simulation box:

    fftool 1 silica-881.xyz -b 40.24,40.24,80,90,90,120 -p xy

Check the number of bonds.

    packmol < pack_fixed.inp
    fftool 1 silica-881.xyz -b 40.24,40.24,80,90,90,120 -p xy -xml -a

This creates input files for OpenMM. Run a short trajectory:

    ./omm-test.py

Visualize the trajectory with vmd:

    vmd -e silica.vmd dump.lammpstrj


## Using LAMMPS to run MD

Only the 2nd step using fftool is different:

    fftool 1 silica-881.xyz -b 40.24,40.24,80,90,90,120 -p xy -l

This creates input files for LAMMPS. Edit `in.lmp` to save one snapshot to the `dump` file every 50 steps and run 5000 steps. Then run:

    mpirun -np 8 lmp -in in.lmp

---
