#!/usr/bin/env python

import sys
import datetime
import numpy as np

import openmm
from openmm import app
from openmm import unit

field = 'field.xml'
config = 'config.pdb'
#statefile = 'state-eq.xml'

temperature = 323.0*unit.kelvin
pressure = (1.0, 1.0, 0.0)

print('#', datetime.datetime.now())
print()

print('#', field, config)
forcefield = app.ForceField(field)
pdb = app.PDBFile(config)

modeller = app.Modeller(pdb.topology, pdb.positions)

print('#  ', modeller.topology.getNumResidues(), 'molecules', modeller.topology.getNumAtoms(), 'atoms', modeller.topology.getNumBonds(), 'bonds')

boxvec = modeller.topology.getPeriodicBoxVectors()
print('# Box vectors (nm):')
print('#     x      y      z')
for vec in boxvec:
    print(f'#   {vec.x:6.2f} {vec.y:6.2f} {vec.z:6.2f}')

system = forcefield.createSystem(modeller.topology, nonbondedMethod=app.PME, nonbondedCutoff=12.0*unit.angstrom, constraints=app.HBonds, ewaldErrorTolerance=1.0e-4)

print('# Langevin integrator', temperature)
integrator = openmm.LangevinIntegrator(temperature, 5/unit.picosecond, 1*unit.femtosecond)

print('#   barostat', pressure)
barostat = openmm.MonteCarloAnisotropicBarostat(pressure, temperature, True, True, False, 5)
system.addForce(barostat)

#platform = openmm.Platform.getPlatformByName('CUDA')
platform = openmm.Platform.getPlatformByName('OpenCL')
#properties = {'DeviceIndex': '1', 'Precision': 'mixed'}
properties = {'Precision': 'single'}

# force settings before creating Simulation
for i, f in enumerate(system.getForces()):
    f.setForceGroup(i)
    if f.getName() == 'HarmonicBondForce':
        f.setUsesPeriodicBoundaryConditions(True)
    if f.getName() == 'HarmonicAngleForce':
        f.setUsesPeriodicBoundaryConditions(True)
    if f.getName() == 'RBTorsionForce':
        f.setUsesPeriodicBoundaryConditions(True)

sim = app.Simulation(modeller.topology, system, integrator, platform, properties)

sim.context.setPositions(modeller.positions)
#sim.context.setVelocitiesToTemperature(temperature)

#print('# coordinates and velocities from', statefile)
#sim.loadState(statefile)

#print('# coordinates and velocities from restart.chk')
#sim.loadCheckpoint('restart.chk')

#state = sim.context.getState()
#sim.topology.setPeriodicBoxVectors(state.getPeriodicBoxVectors())

platform = sim.context.getPlatform()
print('# platform', platform.getName())
for prop in platform.getPropertyNames():
    print('#  ', prop, platform.getPropertyValue(sim.context, prop))

state = sim.context.getState(getEnergy=True)
print('# PotentielEnergy', state.getPotentialEnergy())

for i, f in enumerate(system.getForces()):
    state = sim.context.getState(getEnergy=True, groups={i})
    print('#  ', f.getName(), state.getPotentialEnergy())

print("# Minimizing energy...")
sim.minimizeEnergy()

state = sim.context.getState(getEnergy=True)
print('# PotentielEnergy', state.getPotentialEnergy())

for i, f in enumerate(system.getForces()):
    state = sim.context.getState(getEnergy=True, groups={i})
    print('#  ', f.getName(), state.getPotentialEnergy())

sim.reporters = []
sim.reporters.append(app.StateDataReporter(sys.stdout, 1000, step=True, speed=True, temperature=True, separator='\t', totalEnergy=True, potentialEnergy=True, density=True))
#sim.reporters.append(app.PDBReporter('traj.pdb', 5000))
sim.reporters.append(app.DCDReporter('equil.dcd', 5000))
#sim.reporters.append(app.CheckpointReporter('restart.chk', 10000))

for i in range(1000):
    sim.step(1000)

for i, f in enumerate(system.getForces()):
    state = sim.context.getState(getEnergy=True, groups={i})
    print('#  ', f.getName(), state.getPotentialEnergy())

state = sim.context.getState(getPositions=True, getVelocities=True, getIntegratorParameters=False)
coords = state.getPositions()
sim.topology.setPeriodicBoxVectors(state.getPeriodicBoxVectors())
app.PDBFile.writeFile(sim.topology, coords, open('equil.pdb', 'w'))

sim.context.setTime(0)
sim.context.setStepCount(0)
sim.saveState('state-eq.xml')
print('# state saved to state-eq.xml')
#sim.saveState('state-np.xml')
#print('# state saved to state-np.xml')

print()
print('#', datetime.datetime.now())
