from agents.base import appeler_agent
from config import MODELE_INTERPRETE

PROMPT = """Tu traduis la solution d'un solveur SAT en réponse claire en français.
On te donne le problème d'origine et la liste des affirmations VRAIES dans la solution.
Rédige une réponse directe et naturelle au problème, sans parler de SAT ni de variables.

Règles strictes :
- Les affirmations fournies sont CERTAINES : le solveur les a prouvées. Ne les
  remets jamais en cause, ne les corrige pas, ne les juge pas, même si elles te
  semblent contredire le problème — rapporte-les telles quelles.
- Tu ne conclus « pas de solution » QUE si le message dit AUCUNE SOLUTION.
  Dans ce cas uniquement, explique que les contraintes sont incompatibles."""


def agent_interprete(probleme, formalisation, solution):
    if solution is None:
        faits = ("AUCUNE SOLUTION : le solveur a prouvé que les contraintes "
                 "sont incompatibles.")
    else:
        vraies = [v["description"] for v in formalisation["variables"]
                  if solution[v["nom"]]]
        faits = "Affirmations vraies :\n- " + "\n- ".join(vraies)
    message = f"PROBLÈME :\n{probleme}\n\n{faits}"
    return appeler_agent(MODELE_INTERPRETE, PROMPT, message)
