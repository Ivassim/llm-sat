import json

from agents.base import appeler_agent, formater_remarques
from config import MODELE_VARIABLES

PROMPT = """Tu es un expert en modélisation SAT.
On te donne un problème en langage naturel et la liste de ses entités avec leurs
domaines. Crée les variables booléennes du modèle : typiquement une variable par
couple entité/valeur (par exemple alice_the = « Alice prend du thé »).

Réponds UNIQUEMENT avec un objet JSON de cette forme :
{
  "variables": [
    {"nom": "alice_the", "description": "Alice prend du thé"}
  ]
}

Règles :
- Noms de variables : lettres minuscules, chiffres et _ uniquement, sans accents.
- Chaque variable a une "description" en français, claire et autosuffisante.
- Couvre toutes les combinaisons entité/valeur nécessaires, sans doublon.
- Ne crée aucune variable sans lien avec les entités fournies."""

SCHEMA = {
    "type": "object",
    "properties": {
        "variables": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "nom": {"type": "string"},
                    "description": {"type": "string"},
                },
                "required": ["nom", "description"],
            },
        }
    },
    "required": ["variables"],
}


def agent_variables(probleme, entites, remarques=None):
    message = (f"PROBLÈME :\n{probleme}\n\nENTITÉS ET DOMAINES :\n"
               f"{json.dumps(entites, ensure_ascii=False, indent=2)}"
               + formater_remarques(remarques))
    return appeler_agent(MODELE_VARIABLES, PROMPT, message, SCHEMA)
