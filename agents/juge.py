import json

from agents.base import appeler_agent
from config import MODELE_JUGE

PROMPT = """Tu es un relecteur expert en modélisation SAT. On te donne un problème
et son modèle (JSON). Sémantique : clause/au_moins_un = OU ; au_plus_un ;
exactement_un ; pas_tous = pas tous vrais ; implique = (ET des "si") => (OU des
"alors") ; "!x" = NON x.

Vérifie :
1. Chaque règle du problème (même implicite) est traduite.
2. Chaque contrainte est fidèle : sens de l'implication, négations, cardinalité.
   Pour chaque clause, compare le OU des littéraux TELS QUELS à sa description :
   « si A alors B » doit être (!A OU B) ; (A OU B) décrit comme une implication
   = négation manquante, à signaler.
3. Aucune contrainte qui ne vient d'aucune phrase du problème.

N'est PAS une erreur : un fait de l'énoncé fixé par une contrainte unitaire
(les cardinalités ne fixent pas QUELLE valeur) ; une redondance correcte.
Une erreur change l'ensemble des solutions ; dans le doute, ce n'en est pas une.

Réponds UNIQUEMENT :
{"valide": true ou false,
 "problemes": [{"erreur": "contrainte ou variable fautive, désignée précisément",
   "pourquoi": "en quoi elle trahit l'énoncé",
   "regle_concernee": "la phrase concernée"}]}
Si tout est correct : {"valide": true, "problemes": []}"""

SCHEMA = {
    "type": "object",
    "properties": {
        "valide": {"type": "boolean"},
        "problemes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "erreur": {"type": "string"},
                    "pourquoi": {"type": "string"},
                    "regle_concernee": {"type": "string"},
                },
                "required": ["erreur", "pourquoi"],
            },
        },
    },
    "required": ["valide", "problemes"],
}


def agent_juge(probleme, formalisation):
    message = (f"PROBLÈME :\n{probleme}\n\nMODÈLE SAT :\n"
               f"{json.dumps(formalisation, ensure_ascii=False, indent=2)}")
    return appeler_agent(MODELE_JUGE, PROMPT, message, SCHEMA)
