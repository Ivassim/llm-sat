import json
import sys
import time
from datetime import datetime
from pathlib import Path

from config import DOSSIER_JOURNAL
from pipeline import resoudre_probleme

FICHIER_TESTS = Path("tests") / "tests.json"


class SortieDouble:
    def __init__(self, *flux):
        self.flux = flux

    def write(self, texte):
        for f in self.flux:
            f.write(texte)

    def flush(self):
        for f in self.flux:
            f.flush()


def evaluer_cas(cas):
    print("\n" + "=" * 60)
    print(f"PROBLÈME : {cas['nom']}  (attendu : {cas['attendu']})")
    print("=" * 60)
    debut = time.time()
    resultat = resoudre_probleme(cas["enonce"])
    bilan = {
        "nom": cas["nom"],
        "attendu": cas["attendu"],
        "duree_s": round(time.time() - debut, 1),
        "essais": resultat["essais"],
        "statut_ok": False,
        "solution_ok": None,
        "reponse": resultat["reponse"],
    }

    if resultat["echec"]:
        bilan["obtenu"] = "ECHEC_FORMALISATION"
        return bilan

    bilan["obtenu"] = "UNSAT" if resultat["solution"] is None else "SAT"
    bilan["statut_ok"] = bilan["obtenu"] == cas["attendu"]

    attendue = cas.get("solution_attendue")
    if bilan["statut_ok"] and bilan["obtenu"] == "SAT" and attendue:
        solution = resultat["solution"]
        noms_attendus = [f"{entite}_{valeur}" for entite, valeur in attendue.items()]
        if all(nom in solution for nom in noms_attendus):
            bilan["solution_ok"] = all(solution[nom] for nom in noms_attendus)
        else:
            bilan["solution_ok"] = "non_evaluable"
            bilan["faits_vrais"] = sorted(n for n, v in solution.items() if v)
    return bilan


def afficher_score(bilans):
    print("\n" + "=" * 60)
    print("RÉCAPITULATIF")
    print("=" * 60)
    for b in bilans:
        statut = "✓" if b["statut_ok"] else "✗"
        ligne = (f"{statut} {b['nom']:<24} {b['attendu']:>5} -> {b['obtenu']:<20}"
                 f" essais={b['essais']} durée={b['duree_s']}s")
        if b["solution_ok"] is True:
            ligne += "  solution ✓"
        elif b["solution_ok"] is False:
            ligne += "  SOLUTION FAUSSE"
        elif b["solution_ok"] == "non_evaluable":
            ligne += "  solution à vérifier à la main"
        print(ligne)

    n = len(bilans)
    statuts_ok = sum(1 for b in bilans if b["statut_ok"])
    evaluables = [b for b in bilans if isinstance(b["solution_ok"], bool)]
    solutions_ok = sum(1 for b in evaluables if b["solution_ok"])
    essais_moyens = round(sum(b["essais"] for b in bilans) / n, 2) if n else 0
    duree_totale = round(sum(b["duree_s"] for b in bilans), 1)

    print("-" * 60)
    print(f"Statut (SAT/UNSAT) correct : {statuts_ok}/{n}")
    if evaluables:
        print(f"Solution correcte          : {solutions_ok}/{len(evaluables)} (évaluables)")
    print(f"Essais de formalisation    : {essais_moyens} en moyenne")
    print(f"Durée totale               : {duree_totale}s")
    return {"statuts_ok": statuts_ok, "total": n,
            "solutions_ok": solutions_ok, "solutions_evaluables": len(evaluables),
            "essais_moyens": essais_moyens, "duree_totale_s": duree_totale}


def principal(noms):
    cas_tous = json.loads(FICHIER_TESTS.read_text(encoding="utf-8"))
    cas_choisis = [c for c in cas_tous if not noms or c["nom"] in noms]
    if not cas_choisis:
        print(f"Aucun problème ne correspond à {noms}. "
              f"Disponibles : {', '.join(c['nom'] for c in cas_tous)}")
        return

    dossier = Path(DOSSIER_JOURNAL)
    dossier.mkdir(exist_ok=True)
    horodatage = datetime.now().strftime("%Y-%m-%d_%Hh%Mm%Ss")
    chemin_log = dossier / f"evaluation_{horodatage}.log"

    bilans = []
    with open(chemin_log, "w", encoding="utf-8") as fichier_log:
        sys.stdout = SortieDouble(sys.__stdout__, fichier_log)
        try:
            for c in cas_choisis:
                bilans.append(evaluer_cas(c))
        except KeyboardInterrupt:
            print(f"\n\nInterrompu : {len(bilans)}/{len(cas_choisis)} problèmes évalués.")
        finally:
            if bilans:
                score = afficher_score(bilans)
            sys.stdout = sys.__stdout__

    if not bilans:
        print("Interrompu avant le premier résultat : aucun rapport écrit.")
        return

    chemin = dossier / f"evaluation_{horodatage}.json"
    chemin.write_text(json.dumps({"score": score, "bilans": bilans},
                                 ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nRapport : {chemin}\nLog     : {chemin_log}")


if __name__ == "__main__":
    principal(sys.argv[1:])
