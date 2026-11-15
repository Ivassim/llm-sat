from pysat.card import CardEnc, EncType
from pysat.formula import CNF, IDPool


def compiler_cnf(formalisation):
    pool = IDPool()
    for v in formalisation["variables"]:
        pool.id(v["nom"])
    cnf = CNF()

    def num(lit):
        return -pool.id(lit[1:]) if lit.startswith("!") else pool.id(lit)

    for c in formalisation["contraintes"]:
        t = c["type"]
        if t == "implique":
            # (a ET b) => (c OU d)   <=>   (!a OU !b OU c OU d)
            cnf.append([-num(l) for l in c["si"]] + [num(l) for l in c["alors"]])
            continue
        lits = [num(l) for l in c["litteraux"]]
        if t in ("clause", "au_moins_un"):
            cnf.append(lits)
        elif t == "pas_tous":
            cnf.append([-l for l in lits])
        elif t == "au_plus_un":
            cnf.extend(CardEnc.atmost(lits, bound=1, vpool=pool,
                                      encoding=EncType.seqcounter).clauses)
        elif t == "exactement_un":
            cnf.extend(CardEnc.equals(lits, bound=1, vpool=pool,
                                      encoding=EncType.seqcounter).clauses)
    return cnf, pool
