from agents.base import appeler_agent, formater_remarques
from config import MODELE_ENTITES

PROMPT = """Tu es un analyste expert en modélisation de problèmes logiques.
On te donne un problème en langage naturel. Identifie les entités manipulées
(personnes, objets, cases, créneaux...) et, pour chacune, son domaine : la liste
des valeurs qu'elle peut prendre.

Réponds UNIQUEMENT avec un objet JSON de cette forme :
{
  "entites": [
    {"nom": "alice", "domaine": ["the", "cafe"],
     "description": "Alice choisit une boisson parmi thé et café"}
  ]
}

Règles :
- Noms d'entités et valeurs de domaine : lettres minuscules, chiffres et _ uniquement,
  sans accents.
- N'invente aucune entité ni valeur absente du problème.
- N'oublie aucune entité, y compris celles mentionnées implicitement."""

SCHEMA = {
    "type": "object",
    "properties": {
        "entites": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "nom": {"type": "string"},
                    "domaine": {"type": "array", "items": {"type": "string"}},
                    "description": {"type": "string"},
                },
                "required": ["nom", "domaine", "description"],
            },
        }
    },
    "required": ["entites"],
}


def agent_entites(probleme, remarques=None):
    message = f"PROBLÈME :\n{probleme}" + formater_remarques(remarques)
    return appeler_agent(MODELE_ENTITES, PROMPT, message, SCHEMA)
