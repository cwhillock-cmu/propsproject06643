import pandas as pd
import pyomo.environ as pyo
from idaes_props.engine import PropertyEngine
from idaes.models.properties.general_helmholtz import AmountBasis

def test_logic():
    engine = PropertyEngine('co2', amount_basis=AmountBasis.MOLE)
    model = engine.model
    model.stateblock1 = model.properties.build_state_block(defined_state=True, has_phase_equilibrium=True)
    model.obj = pyo.Objective(expr=0)
    model.stateblock1.flow_mol.fix(1)
    model.stateblock1.pressure.fix(101325)
    model.T_constraint = pyo.Constraint(expr=model.stateblock1.temperature == 298.15)
    
    engine.solve()
    state = model.stateblock1
    
    data = {}
    
    # Determine phase
    vfrac = pyo.value(state.vapor_frac)
    if vfrac >= 0.9999:
        data['phase_id'] = 'Vap'
    elif vfrac <= 0.0001:
        data['phase_id'] = 'Liq'
    else:
        data['phase_id'] = 'Mix'
        
    props = ['temperature', 'pressure', 'dens_mol_phase']
    for p in props:
        prop_obj = getattr(state, p)
        if prop_obj.is_indexed():
            # Assume it's indexed by phase or component
            for idx in prop_obj.index_set():
                val = pyo.value(prop_obj[idx])
                # format index nicely (tuple if multiple indices)
                idx_str = "_".join(str(i) for i in idx) if isinstance(idx, tuple) else str(idx)
                data[f"{p}_{idx_str}"] = val
        else:
            data[p] = pyo.value(prop_obj)
            
    df = pd.DataFrame([data])
    print(df)

if __name__ == '__main__':
    test_logic()