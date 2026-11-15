import json
from datetime import datetime
from pathlib import Path

from agents.entites import agent_entites
from agents.interprete import agent_interprete
from agents.juge import agent_juge
from agents.regles import agent_regles
from agents.variables import agent_variables
from config import DOSSIER_JOURNAL, MAX_ESSAIS
from sat.controle import controler_solution
from sat.solveur import resoudre
from sat.syntaxe import verifier_syntaxe


def assembler(variables, contraintes):
    return {"variables": variables["variables"],
            "contraintes": contraintes["contraintes"]}


def ecrire_journal(journal):
    dossier = Path(DOSSIER_JOURNAL)
    dossier.mkdir(exist_ok=True)
    chemin = dossier / datetime.now().strftime("%Y-%m-%d_%Hh%Mm%Ss.json")
    chemin.write_text(json.dumps(journal, ensure_ascii=False, indent=2),
                      encoding="utf-8")
    return chemin


def resoudre_probleme(probleme):
    """Renvoie {"echec", "essais", "formalisation", "solution", "contraintes_violees", "reponse"}."""
    journal = {"probleme": probleme, "iterations": [], "solution": None,
               "contraintes_violees": None, "reponse": None}
    remarques = None
    formalisation = None

    for essai in range(1, MAX_ESSAIS + 1):
        iteration = {"essai": essai, "remarques_recues": remarques}

        try:
            print(f"\n[1] Identification des entités (essai {essai}/{MAX_ESSAIS})...")
            entites = agent_entites(probleme, remarques)
            iteration["entites"] = entites
            print(f"    {len(entites.get('entites', []))} entités")

            print("[2] Définition des variables booléennes...")
            variables = agent_variables(probleme, entites, remarques)
            iteration["variables"] = variables
            print(f"    {len(variables.get('variables', []))} variables")

            print("[3] Traduction des règles en contraintes...")
            contraintes = agent_regles(probleme, variables, remarques)
            iteration["contraintes"] = contraintes
            print(f"    {len(contraintes.get('contraintes', []))} contraintes")
        except ValueError as exc:
            print(f"    ✗ {exc}")
            iteration["erreur_appel"] = str(exc)
            journal["iterations"].append(iteration)
            remarques = ["Ta réponse précédente était vide ou n'était pas un JSON "
                         "valide. Réponds uniquement avec l'objet JSON demandé."]
            continue

        formalisation = assembler(variables, contraintes)

        print("[4] Vérification syntaxique...")
        erreurs = verifier_syntaxe(formalisation)
        iteration["erreurs_syntaxe"] = erreurs
        if erreurs:
            print("    ✗ " + "\n    ✗ ".join(erreurs))
            remarques = erreurs
            journal["iterations"].append(iteration)
            continue
        print("    ✓ OK")

        print("[5] Jugement de la correspondance problème <-> modèle...")
        try:
            verdict = agent_juge(probleme, formalisation)
        except ValueError as exc:
            print(f"    ✗ {exc}")
            iteration["erreur_appel"] = str(exc)
            journal["iterations"].append(iteration)
            remarques = None
            continue
        iteration["verdict_juge"] = verdict
        journal["iterations"].append(iteration)
        if not verdict.get("valide", False):
            remarques = verdict.get("problemes") or [
                {"erreur": "Le modèle ne correspond pas au problème.",
                 "pourquoi": "Le juge l'a rejeté sans détail."}]
            for p in remarques:
                print(f"    ✗ {p.get('erreur', p)}")
            continue
        print("    ✓ Le modèle correspond au problème")
        break
    else:
        print("\nÉchec : aucun modèle valide après plusieurs essais.")
        chemin = ecrire_journal(journal)
        print(f"Journal : {chemin}")
        return {"echec": True, "essais": MAX_ESSAIS, "formalisation": formalisation,
                "solution": None, "contraintes_violees": [], "reponse": None}

    print("[6] Résolution SAT (export DIMACS : probleme.cnf)...")
    solution = resoudre(formalisation)
    journal["solution"] = solution
    violees = []
    if solution is None:
        print("    UNSAT : aucune solution")
    else:
        print("    SAT : " + ", ".join(n for n, val in solution.items() if val))
        print("[7] Contrôle de la solution...")
        violees = controler_solution(formalisation, solution)
        journal["contraintes_violees"] = violees
        print("    ✓ Toutes les contraintes sont respectées" if not violees
              else "    ✗ Contraintes violées : " + "; ".join(violees))

    print("[8] Interprétation...")
    reponse = agent_interprete(probleme, formalisation, solution)
    journal["reponse"] = reponse
    chemin = ecrire_journal(journal)

    print("\n================ RÉPONSE ================\n" + reponse)
    print(f"\nJournal : {chemin}")
    return {"echec": False, "essais": essai, "formalisation": formalisation,
            "solution": solution, "contraintes_violees": violees,
            "reponse": reponse}
