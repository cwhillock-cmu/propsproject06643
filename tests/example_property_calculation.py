import pyomo.environ as pyo # Pyomo environment
from idaes.models.properties.general_helmholtz import (
    HelmholtzParameterBlock,
    PhaseType,
    StateVars,
    AmountBasis,
)

Temperature = 298 #K
Pressure = 2*100000 #Pa

# Create a parameter block and state block
model = pyo.ConcreteModel()
model.properties = HelmholtzParameterBlock(
  pure_component="co2", #get list of available components with idaes.models.properties.general_helmholtz.registered_components()
  phase_presentation=PhaseType.LG, #most robust option
  state_vars=StateVars.PH, #alternative is TPX formulation, but that is less robust around phase changes
  amount_basis=AmountBasis.MOLE, #can be AmountBasis.MOLE or AmountBasis.MASS, changes how to reference variables later, eg enth_mol or enth_mass
)
model.stateblock1 = model.properties.build_state_block(defined_state=True,has_phase_equilibrium=True)
#can add multiple stateblocks to model to solve multiple states at the same time

model.obj = pyo.Objective(expr=0) #dummy objective
model.stateblock1.flow_mol.fix(1) #fix this to 1, no extensive calculations

#in PH formulation (set with StateVars.PH), pressure and enthalpy are variables, fix pressure and add constraint to temperature
model.stateblock1.pressure.fix(Pressure)
model.T_constraint = pyo.Constraint(expr=model.stateblock1.temperature==Temperature)

solver = pyo.SolverFactory('ipopt')
solver.solve(model,tee=False)

#retrieve values
print(f'temperature={pyo.value(model.stateblock1.temperature)}')
print(f'enthalpy={pyo.value(model.stateblock1.enth_mol)}')
print(f'entropy={pyo.value(model.stateblock1.entr_mol)}')
#can also get values of expressions
print(f'isobaric heat capacity={pyo.value(model.stateblock1.cp_mol)}')