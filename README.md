# Simulation of ionic liquids at interfaces

## Objectives

The following examples use molecular dynamics (MD) simulations to study the interfaces between ionic liquids and materials. THe level of description if all-atom, fully flexible interaction potentials.

These examples of application should allow you to develop skills in modelling heterogeneous systems at the atomistic level and in computing some of their properties, for example the structure of the interfacial layers (easy) or the capacitance of a charged interface (more challenging).

Detailed guidelines are given on how to build periodic systems containing a slab of a material and a film of liquid. The aim is to learn how to build such systems from scratch, equilibrate them, run a trajectory, and finally compute some properties in post-treatment.

You are encouraged to go beyond the provided examples and test novel things (different system sizes, other ions) or compute different quantities (lifetimes in the interfacial layers). More challenging targets are also suggested, namely studying charged interfaces.

The MD code used here is OpenMM, accessed through its Python interface. This is a modern code, very efficient on GPU processors. Some trajectory analysis tools are also provided as Python notebooks.

Input files for two ionic liquids based on imidazolium cations with different alkyl side-chain lengths, and two materials — graphite and silica — are supplied.

----

## Requirements

- [OpenMM](https://openmm.org), molecular dynamics code that is mostly used through its Python interface
- [Packmol](https://m3g.github.io/packmol/), packs molecules in a box
- [VMD](https://www.ks.uiuc.edu/Research/vmd/), trajectory visualizer
- [VESTA](https://jp-minerals.org/vesta/en/), visualizer and editor of crystallographic files
- [fftool](https://github.com/paduagroup/fftool), builds an initial configuration and the force field for a system
- [clandp](https://github.com/paduagroup/clandp), force field for ionic liquids

### Access to the codes and tools

The codes and tools are installed on the machines of the CBP and PSMN computing centers.

To access OpenMM one needs to activate the following conda environment:

    conda activate openmm

If this does not work, you'll need to include the contents of the `/projects/DepartementChimie/conda.rc` file in your `.bashrc`.

To use fftool, add `/projects/DepartementChimie/fftool` to your `PATH` in `.bashrc` or `.profile`.

If you need to use additional molecule input files with the clandp force field, you can download it from [github.com/paduagroup](https://github.com/paduagroup) 


----

## Simple system with single-phase ionic liquid

As a first simple system, to familiarize yourself with the tools and codes, simulate an ionic liquid in a cubic box.

### Build initial configuration and force field

Learn about the options of fftool:

    fftool -h

Then cd to the `mols` folder and build a box of density 5.0 mol/L (somewhat below the experimental density to give ions room to equilibrate):

    fftool 300 c2c1im.zmat 300 BF4.zmat --rho 5.0

This step creates an input file for Packmol, `pack.inp`. Familiarize yourself with this file. Use Packmol to place the molecules in a box and visualize:

    packmol < pack.inp
    vmd simbox.xyz
    
In the second step of fftool provide the `--xml` option to produce input files for OpenMM:

    fftool 300 c2c1im.zmat 300 BF4.zmat --rho 5.0 --xml

Create a new folder to run a short simulation there:

    mkdir ../c2mim_bf4
    cp field.xml config.pdb omm.py ../c2mim_bf4
    cd ../c2mim_bf4


### Run simulations

Check the GPUs on your computer:

    nvidia-smi

Edit `omm.py` to check settings concerning simulation conditions, integrators, long-range interactions, GPU choice, initial minimization, number of steps, etc.

Run a test trajectory of a few ps:

    ./omm.py &> omm.out &

Use `cat omm.out` or `tail -f omm.out` to follow the progress of the simulation. 

Once it's done visualize:

    vmd -e ../mols/il.vmd config.pdb traj.dcd

Run an equilibration (maybe 1 ns) at 323 K. Adapt the reporters, since there is no need to save configurations to the trajectory or print to screen so often. Check the convergence of the density in the `omm.out` file. 

If not converged, continue the equilibration from the state saved in `state-eq.xml`.

Starting from an equilibrated state, run an acquisition trajectory of 2 ns.

Analysis notebooks (using MDTraj and similar tools) are available to compute some structural or transport quantities, such as radial distribution functions and diffusion coefficients.

### Scaling ionic charges

In ionic systems, force fields with integer ionic charges often lead to slow dynamics. A fix for that is to scale ionic charges by 0.8 (see the code snippet in `scaleq.py`). You can try this and see the effect on the density and the diffusion coefficients.

It is probably a good idea to use scaled charges in the following examples to speed up dynamics.


----


## Graphite with ionic liquid

In this section we build and simulate a system consisting of graphene planes with a film of ionic liquid. There will be several interfaces, namely between the material and IL, and the free surface of the IL.

Although the unit cell of graphite corresponds to an hexagonal lattice, we will work with an orthorhombic (all angles 90°) simulation box.


### Create graphene planes from crystal structure

Download a CIF file for graphite from the [Crystallography Open Database](https://www.crystallography.net/): 9011577.cif


Using VESTA, under \<Edit\>\<Bonds\> choose each bond type on the table (there is just one type for graphite) and tick \<Do not search atoms beyond the boundary\>, then \<Apply\>.

Click \<Boundary...\> and set ranges of fractional coordinates: x(max) = 26.4, y(max) = 19.9, z(max) = 1.

Add cutoff planes:

- (2 -1 0), distance from origin 33 x d
- (-2 1 0), distance from origin 0.1 x d

Verify that the edges of the graphene planes are matching, with no duplicate atoms (only the bonds across box boundaries should be missing).

Q. Count the number of unit calls along each perpendicular direction.

Check that you have 680 atoms per plane. You can choose z(max) to control the number of planes. For the following work we will use 4 planes, so set z(max) accordingly.

Then \<Export Data...\> to XYZ format (do not save hidden atoms).

### Simulation box with periodic graphene planes

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
    fftool 1 graph.xyz --box 41.888,42.678,50 --pbc xy


The `gr_pack.inp` file instructs Packmol to place the structure fixed at the origin:

    packmol < gr_pack.inp

Create the input files for OpenMM:

    fftool 1 graph.xyz --box 41.888,42.678,50 --pbc xy --xml

With the planes stitched across box boundaries we expect 1.5 * 2720 = 4080 bonds.

Test a short run with just the graphene planes:

    cp field.xml config.pdb omm.py../graph
    cd ../graph

Graphite atoms have no electrostatic charge, therefore edit the `omm-test.py` file to replace the `createSystem()` line with just:

        system = forcefield.createSystem(modeller.topology, nonbondedCutoff=12.0*unit.angstrom)

Then run

    ./omm.py

Check energies and density to see if the box size adapts.

    vmd -e ../mols/graph.vmd config.pdb traj.dcd


### Add ionic liquid

Put 300 ion pairs of $\mathrm{[C_2C_1im][BF4]}$ above the graphene planes:

    cd mols
    fftool 1 graph.xyz 300 c2c1im.zmat 300 BF4.zmat --box 41.888,42.678,100
    packmol < gr_c2_pack.inp
    vmd simbox.xyz

    fftool 1 graph.xyz 300 c2c1im.zmat 300 BF4.zmat --box 41.888,42.678,100 --pbc xy --xml

Copy the `field.xml`, `config.pdb` and `omm.py` files to a new folder, then run a short test trajectory to make sure the system is ok:

    ./omm.py &> omm.out &

Visualize:

    vmd -e ../mols/graph.vmd config.pdb traj.dcd

Then run an equilibration of 1 ns at 323 K; visualize it using vmd;
check values of energy to see if the system is well equilibrated; run a trajectory from its last configuration for 4 ns saving a snapshot every 1000 steps (4000 configurations).

Repeat with $\mathrm{[C_8C_1im][BF_4]}$. Create a copy of `gr_c2_pack.inp` suitable for c8c1im using less ion pairs (200 for example), in order to have comparable numbers of atoms for the two ionic liquids.


----


## Silica surface

In this section we will build a system with a silica slab and ionic liquid. The box will not be orthorhombic.


### Build silica slab

Open the file `POSCAR-SiO2-hydr` with VESTA. In \<Edit\>\<Bonds\>, for each bond type, select not to search atoms beyond the boundary.

Study the unit cell (lengths, angles, composition). It has 36 atoms and 44 bonds (check the types of bonds and angles and compare with the force field in `silica.ff`). This is important information to verify that, once we construct a simulation box, bonds across periodic boundaries are correctly accounted for.

In Boundary set a 8 x 8 x 1 supercell and export to XYZ format. (You can start with a smaller supercell and attempt a larger one when more familiar with the silica structure.)

Edit the .xyz file:
- Set the force field file (`silica.ff`) as the second token in the second line;
- Change all H atom names to HO.
- Identify the O atoms near the surface (by their z values) and set their types to OH.

Verify that their numbers are identical:

    grep HO silica-881.xyz | wc -l
    grep OH silica-881.xyz | wc -l

Use fftool to prepare a simulation box:

    fftool 1 silica-881.xyz --box 40.24,40.24,80,90,90,120 --pbc xy

Check that the number of bonds is correct.

    packmol < pack_fixed.inp
    fftool 1 silica-881.xyz --box 40.24,40.24,80,90,90,120 --pbc xy --xml

This creates input files for OpenMM. Run a short trajectory to test:

    ./omm.py

Visualize the trajectory with vmd:

    vmd -e silica.vmd config.pdb traj.dcd


## Add ionic liquid

Add ionic liquid above the silica slab, similarly to what was done with the graphene systems.

Use boxes with about $L_z = 120\ \AA$. Then use packmol with the input file `si_c2_pack.inp` (study this file for the instructions to pack molecules in a cell which is not orthorhombic).

Run a short trajectory to see if the system is stable.

Redo with $\mathrm{[C_8C_1im][BF_4]}$ allowing for sufficient volume to place the ions in the packmol input file.

---


# Charged electrode surfaces

One more challenging application consists of simulating parallel-plate electrodes with ionic liquid, applying a given charge density to the electrodes (of opposite signs to keep the overall box neutral).

Such a system can be setup and equilibrated following the procedures learned previously.

The charge density profile is an interesting quantity to compute, and from this the electric potential can be calculated through integration.

