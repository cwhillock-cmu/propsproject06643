import logging
import pyomo.environ as pyo
from idaes.models.properties.general_helmholtz import (
    HelmholtzParameterBlock,
    PhaseType,
    StateVars,
    AmountBasis,
    registered_components,
)
from pyomo.common.errors import PyomoException

logger = logging.getLogger(__name__)

def validate_component(component: str) -> None:
    """
    Validates that the provided component is supported by the IDAES Helmholtz EOS.
    Raises ValueError if not supported.
    """
    valid = registered_components()
    if component not in valid:
        raise ValueError(
            f"Component '{component}' is not supported. "
            f"Supported components include: {valid}"
        )


class PropertyEngine:
    """
    Core engine for IDAES physical property calculations using the Helmholtz EOS.
    """
    def __init__(self, component: str, amount_basis=AmountBasis.MOLE):
        validate_component(component)
        self.component = component
        self.amount_basis = amount_basis
        self.model = pyo.ConcreteModel()
        
        # Configure the parameter block for the pure component
        self.model.properties = HelmholtzParameterBlock(
            pure_component=component,
            phase_presentation=PhaseType.LG,
            state_vars=StateVars.PH,      # Pressure-Enthalpy formulation (more robust)
            amount_basis=amount_basis,
        )
        self.solver = pyo.SolverFactory('ipopt')
        self.solver.options['linear_solver']='ma57'

    def solve(self) -> bool:
        """
        Solves the constructed model.
        Returns True if successful, False otherwise.
        """
        try:
            logger.debug(f"Solving {self.component} property model...")
            #self.model.pprint()
            results = self.solver.solve(self.model, tee=False)
            
            # Check solver termination condition
            if results.solver.termination_condition != pyo.TerminationCondition.optimal:
                logger.error(f"Solver failed to converge optimally. Status: {results.solver.status}, "
                             f"Termination condition: {results.solver.termination_condition}")
                return False
                
            return True
        except (ValueError, PyomoException) as e:
            logger.error(f"Solver encountered an error during solve: {e}")
            return False
