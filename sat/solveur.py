from pysat.solvers import Solver

from config import FICHIER_CNF
from sat.compilation import compiler_cnf


def resoudre(formalisation):
    """{nom_variable: bool} si SAT, None si UNSAT."""
    cnf, pool = compiler_cnf(formalisation)
    cnf.to_file(FICHIER_CNF)
    with Solver(name="glucose4", bootstrap_with=cnf.clauses) as solveur:
        if not solveur.solve():
            return None
        vraies = {x for x in solveur.get_model() if x > 0}
    return {v["nom"]: pool.id(v["nom"]) in vraies
            for v in formalisation["variables"]}
