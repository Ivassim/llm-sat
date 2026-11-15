def valeur(lit, solution):
    return not solution[lit[1:]] if lit.startswith("!") else solution[lit]


def controler_solution(formalisation, solution):
    violees = []
    for c in formalisation["contraintes"]:
        t = c["type"]
        if t == "implique":
            ok = (not all(valeur(l, solution) for l in c["si"])
                  or any(valeur(l, solution) for l in c["alors"]))
        else:
            n = sum(valeur(l, solution) for l in c["litteraux"])
            ok = {"clause": n >= 1, "au_moins_un": n >= 1, "au_plus_un": n <= 1,
                  "exactement_un": n == 1,
                  "pas_tous": n < len(c["litteraux"])}[t]
        if not ok:
            violees.append(c.get("description", str(c)))
    return violees
