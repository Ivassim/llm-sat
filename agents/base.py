import json
import ollama
from config import OPTIONS


def appeler_agent(modele, consigne, message, schema=None):

    reponse = ollama.chat(
        model=modele,
        messages=[{"role": "system", "content": consigne},
                  {"role": "user", "content": message}],
        format=schema,
        options=OPTIONS,
    )
    texte = (reponse.message.content or "").strip()
    if schema is None:
        return texte
    if not texte:
        raise ValueError(
            f"Le modèle {modele} a renvoyé une réponse vide "
            f"(done_reason={getattr(reponse, 'done_reason', None)}).")
    try:
        return json.loads(texte)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Réponse non-JSON du modèle {modele} : {texte[:200]!r}") from exc


def formater_remarques(remarques):
    
    if not remarques:
        return ""
    lignes = []
    for r in remarques:
        if isinstance(r, dict):
            ligne = r.get("erreur", "")
            if r.get("pourquoi"):
                ligne += f" — pourquoi : {r['pourquoi']}"
            if r.get("regle_concernee"):
                ligne += f" (règle concernée : {r['regle_concernee']})"
            lignes.append(ligne)
        else:
            lignes.append(str(r))
    return ("\n\nUne version précédente de la formalisation contenait ces erreurs, "
            "corrige-les :\n- " + "\n- ".join(lignes))
