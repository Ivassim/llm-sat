import json

from agents.base import appeler_agent, formater_remarques
from config import MODELE_REGLES

PROMPT = """Tu es un expert en modélisation SAT. Traduis chaque règle du problème
en contraintes sur les variables fournies. Littéral = nom de variable ou "!nom".

Réponds UNIQUEMENT avec ce JSON :
{
  "contraintes": [
    {"type": "exactement_un", "litteraux": ["alice_the", "alice_cafe"],
     "description": "Alice prend exactement une boisson"}
  ],
  "implications": [
    {"si": ["chloe_the"], "alors": ["bob_cafe"],
     "description": "Si Chloé prend du thé, alors Bob prend du café"}
  ]
}

Types de "contraintes" : clause / au_moins_un (OU), au_plus_un, exactement_un,
pas_tous (pas tous vrais à la fois).
"implications" : (ET des "si") => (OU des "alors"). Toute règle « si... alors... »
va ici, jamais en clause. « si A alors B et C » = 2 implications ;
« A si et seulement si B » = 2 implications (les deux sens).
Traduis chaque phrase par son encodage direct, sans reformuler :
« X et Y ne choisissent pas pareil » = un pas_tous par valeur
(["x_the", "y_the"] puis ["x_cafe", "y_cafe"]), sans implication.
Chaque élément cite en "description" la phrase qu'il traduit. N'oublie aucune
règle, même implicite (« chacun a exactement une boisson »)."""

CONTRAINTE_SIMPLE = {
    "type": "object",
    "properties": {
        "type": {"type": "string",
                 "enum": ["clause", "au_moins_un", "au_plus_un",
                          "exactement_un", "pas_tous"]},
        "litteraux": {"type": "array", "items": {"type": "string"},
                      "minItems": 1},
        "description": {"type": "string"},
    },
    "required": ["type", "litteraux", "description"],
}
IMPLICATION = {
    "type": "object",
    "properties": {
        "si": {"type": "array", "items": {"type": "string"}, "minItems": 1},
        "alors": {"type": "array", "items": {"type": "string"}, "minItems": 1},
        "description": {"type": "string"},
    },
    "required": ["si", "alors", "description"],
}
SCHEMA = {
    "type": "object",
    "properties": {
        "contraintes": {"type": "array", "items": CONTRAINTE_SIMPLE},
        "implications": {"type": "array", "items": IMPLICATION},
    },
    "required": ["contraintes", "implications"],
}


def agent_regles(probleme, variables, remarques=None):
    message = (f"PROBLÈME :\n{probleme}\n\nVARIABLES BOOLÉENNES :\n"
               f"{json.dumps(variables, ensure_ascii=False, indent=2)}"
               + formater_remarques(remarques))
    brut = appeler_agent(MODELE_REGLES, PROMPT, message, SCHEMA)
    contraintes = list(brut.get("contraintes", []))
    for imp in brut.get("implications", []):
        contraintes.append({"type": "implique", "si": imp["si"],
                            "alors": imp["alors"],
                            "description": imp["description"]})
    return {"contraintes": contraintes}
