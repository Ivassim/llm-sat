from config import TYPES_CONTRAINTES


def nom_du_litteral(lit):
    return lit[1:] if lit.startswith("!") else lit


def verifier_syntaxe(formalisation):
    erreurs = []
    if not isinstance(formalisation, dict):
        return ["La formalisation n'est pas un objet JSON."]
    variables = formalisation.get("variables")
    contraintes = formalisation.get("contraintes")
    if not isinstance(variables, list) or not variables:
        return ["Il manque la liste 'variables'."]
    if not isinstance(contraintes, list) or not contraintes:
        return ["Il manque la liste 'contraintes'."]

    noms = set()
    for v in variables:
        nom = v.get("nom") if isinstance(v, dict) else None
        if not nom or not isinstance(nom, str):
            erreurs.append(f"Variable mal formée : {v}")
        elif nom in noms:
            erreurs.append(f"Variable déclarée deux fois : {nom}")
        else:
            noms.add(nom)

    for i, c in enumerate(contraintes):
        if not isinstance(c, dict):
            erreurs.append(f"Contrainte {i} mal formée.")
            continue
        t = c.get("type")
        if t not in TYPES_CONTRAINTES:
            erreurs.append(f"Contrainte {i} : type inconnu '{t}'.")
            continue
        if t == "implique":
            groupes = [c.get("si"), c.get("alors")]
            if not all(isinstance(g, list) and g for g in groupes):
                erreurs.append(f"Contrainte {i} (implique) : 'si' et 'alors' "
                               "doivent être des listes non vides.")
                continue
            litteraux = groupes[0] + groupes[1]
        else:
            litteraux = c.get("litteraux")
            if not isinstance(litteraux, list) or not litteraux:
                erreurs.append(f"Contrainte {i} : 'litteraux' doit être une "
                               "liste non vide.")
                continue
        for lit in litteraux:
            if not isinstance(lit, str) or nom_du_litteral(lit) not in noms:
                erreurs.append(f"Contrainte {i} : variable non déclarée '{lit}'.")
    return erreurs
