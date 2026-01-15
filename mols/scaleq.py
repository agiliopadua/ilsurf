# use this snipped of code to scale charges (after creation of system)
scaleq = 0.8

for force in system.getForces():
    if isinstance(force, openmm.NonbondedForce):
        for i in range(force.getNumParticles()):
            q, sig, eps = force.getParticleParameters(i)
            force.setParticleParameters(i, scaleq * q, sig, eps)
