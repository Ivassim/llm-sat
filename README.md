# ia-driven-sat

Pipeline agentique qui traduit un probleme logique enonce en francais en modele SAT, le resout avec un solveur exact (pysat), puis retraduit la solution en francais

> **Les LLM traduisent, le code verifie, le solveur decide**

## D'ou vient l'idee

En regardant une video ou un createur joue une partie d'echecs contre ChatGPT, on voit le modele proposer des coups illegaux, alors que les regles sont simples et connues. Le modele "parle" des echecs sans jamais verifier ce qu'il avance

Le projet part de ce constat : un LLM est un bon traducteur (langage naturel vers structure formelle), mais un mauvais juge de sa propre coherence. Au lieu de lui demander la reponse directement, on lui fait produire un **modele formel**, puis on laisse du code deterministe et un solveur exact verifier et trancher. Un coup illegal ou une solution fausse ne peut plus passer inapercu : le controle est fait par du code, pas par un LLM

## Principe et architecture

```
Probleme en francais
   │
   ▼
[Agent entites] ─► [Agent variables] ─► [Agent regles]        agents/ (LLM)
   │                    │                    │
   └────────────────────┴────────────────────┘
                        ▼
              formalisation JSON (assemblage, code pur)
                        ▼
              validation syntaxique (code pur)                 sat/
                        ▼
              [Agent juge] ── non ──► rapport d'erreurs ──► renvoye aux 3 agents
                        │ oui                                  (boucle, MAX_ESSAIS = 3)
                        ▼
              compilation CNF + solveur pysat (code pur)
                        ▼
              controle de la solution (code pur)
                        ▼
              [Agent interprete] ─► reponse en francais
```

- **Les LLM ne font que la traduction** : identifier les entites, definir les variables booleennes, convertir les regles en contraintes, juger la correspondance, reformuler la solution
- **Tout ce qui est verifiable par du code** ne passe jamais par un LLM : syntaxe, encodage CNF, resolution, controle de la solution
- **Sorties structurees** : chaque agent qui produit des donnees repond selon un schema JSON impose a Ollama, ce qui elimine les erreurs de syntaxe. La boucle de correction ne sert qu'aux erreurs de sens
- **Le juge designe et explique** chaque erreur (contrainte ou variable fautive, et en quoi elle trahit l'enonce). Son rapport est renvoye au bloc de formalisation entier

Format intermediaire (contrat entre agents et solveur) :

```json
{
  "variables": [{"nom": "alice_the", "description": "Alice prend du the"}],
  "contraintes": [
    {"type": "exactement_un", "litteraux": ["alice_the", "alice_cafe"],
     "description": "Alice prend exactement une boisson"}
  ]
}
```

Types de contraintes : `clause`, `au_moins_un`, `au_plus_un`, `exactement_un`, `pas_tous`, `implique`. Chaque contrainte porte une `description` qui cite la phrase de l'enonce qu'elle traduit. C'est le lien entre l'enonce et le modele, que le juge utilise

## Contraintes materielles et choix des modeles

La machine de test dispose de **8 Go de VRAM**. Pour que les modeles tiennent entierement sur le GPU :

- les **poids** sont en quantification **Q4**
- le **cache KV** (contexte) est en quantification **Q8**
- `num_ctx` est fixe a 16384 tokens

Ce sont des modeles de petite taille (4 a 9 milliards de parametres). Ils sont donc **moins capables que les modeles de reference** : la quantification reduit la precision des poids, et la taille limite le raisonnement. Une partie des echecs observes vient de la. Le pipeline est concu pour compenser cette faiblesse en decoupant la tache et en verifiant chaque etape par du code, plutot qu'en comptant sur un seul modele puissant

**Pourquoi des modeles differents selon l'etape** (voir `config.py`) :

| Etape | Modele | Raison |
|---|---|---|
| Entites | `qwen3.5:4b` | Tache courte et simple, un petit modele suffit |
| Variables | `qwen3.5:4b` | Idem |
| Regles | `qwen3.5:9b-U` | Tache la plus difficile : le plus gros modele |
| Juge | `deepseek-r1:8b` | **Doit etre different des formalisateurs** : un modele relit mal son propre travail |
| Interprete | `qwen3.5:4b` | Reformulation simple |

Un seul modele est charge a la fois : le pipeline est sequentiel, et on accepte le temps de rechargement entre deux modeles en echange du meilleur modele par etape, sans contrainte de VRAM cumulee. Les temperatures sont basses (0.2) pour la formalisation et le juge, afin d'obtenir de la stabilite plutot que de la creativite

Tout tourne en local via Ollama : aucune donnee ne quitte la machine

## Resultats de l'evaluation

Evaluation sur 12 problemes de `tests/tests.json` (journal : `journal/evaluation_2026-11-14_10h40m48s.json` et `.log`)

| Probleme | Attendu | Obtenu | Essais | Solution |
|---|---|---|---|---|
| plats | SAT | SAT | 1 | ✓ |
| couleurs | SAT | SAT | 1 | ✓ |
| desserts | SAT | ECHEC_FORMALISATION | 3 | — |
| boissons | SAT | SAT | 1 | ✓ |
| chevaliers_et_fripons | SAT | ECHEC_FORMALISATION | 3 | — |
| triangle_2_couleurs | UNSAT | UNSAT | 2 | — |
| triangle_3_couleurs | SAT | SAT | 1 | ✓ |
| pigeons | UNSAT | UNSAT | 1 | — |
| planning | SAT | SAT | 2 | ✓ |
| einstein_mini | SAT | ECHEC_FORMALISATION | 3 | — |
| einstein_contradictoire | UNSAT | ECHEC_FORMALISATION | 3 | — |
| fete_ambigue | SAT | SAT | 2 | ✓ |

**Bilan :**

- Statut SAT/UNSAT correct : **8 / 12**
- Solution correcte : **4 / 4** (sur les problemes SAT dont la solution est evaluable)
- Essais de formalisation en moyenne : **1,92**
- Duree totale : **5 408 s** (environ 90 min)

Ce que disent ces chiffres :

- **Quand la formalisation aboutit, le resultat est juste.** Les 8 verdicts obtenus sont corrects, et les solutions SAT sont verifiees par le controle deterministe. Les deux UNSAT (triangle a 2 couleurs, pigeons) sont bien detectes par le solveur
- **Les 4 echecs sont tous des echecs de formalisation**, pas des erreurs du solveur. Le pipeline s'arrete proprement et le signale. Il n'affirme jamais une reponse fausse dans ces cas
- **Causes observees des echecs :**
  - *Reponses vides* (`done_reason=length`) : le modele s'arrete sans produire de sortie, 12 fois sur l'ensemble de l'evaluation. Probablement lie a la taille du contexte et a la quantification, mais a confirmer
  - *Rejets par le juge* : sur `desserts`, `chevaliers_et_fripons` et `einstein_mini`, le juge a releve une clause incorrecte ou manquante. Il a donc fonctionne comme prevu, mais ses critiques ne suffisent pas toujours a faire corriger le modele en trois essais
- **Les problemes les plus gros** (`einstein_*`, 9 a 18 variables et de nombreuses implications) sont les plus difficiles pour de petits modeles : ce sont eux qui echouent le plus souvent

## Limites

- **Ce pipeline ne traite pas la planification au sens strict.** Un probleme de planification consiste a trouver une *suite d'actions* qui fait passer d'un etat initial a un etat final, avec des etats successifs et un horizon temporel. Le format JSON ne contient ni variables indexees par le temps, ni notion d'etape, ni axiomes de persistance. Il faudrait un encodage dedie (type SAT planning) qui n'existe pas ici
- Le test `planning` passe, mais c'est un **probleme d'affectation** : quatre reunions a placer sur deux creneaux fixes, avec des conflits. Ce type de probleme rentre dans le format. Ce n'est pas une preuve de capacite a planifier
- **Pas de raisonnement arithmetique ni d'ordre** au-dela de ce que les clauses permettent : `einstein_*` demande de traduire "juste a droite de", ce qui reste fragile
- **Les modeles sont petits et quantifies**, donc la formalisation est le point faible. Le juge et la boucle corrigent une partie des erreurs, pas toutes
- **Les problemes ambigus** (`fete_ambigue`) ne sont pas traites comme tels : le pipeline choisit une lecture, sans la signaler

## Installation et utilisation

Python 3.11+, [Ollama](https://ollama.com) lance, et les modeles listes dans `config.py` telecharges

```bash
python -m venv .venv
.venv\Scripts\activate
pip install ollama python-sat
```

```bash
python main.py                      # exemple integre
python main.py "ton probleme..."    # probleme libre
```

Chaque execution ecrit un journal JSON dans `journal/` (appels, rapports du juge, CNF, solution). Le fichier `probleme.cnf` est exporte au format DIMACS pour le debogage

## Structure du projet

```
config.py            # modeles Ollama par agent, OPTIONS, MAX_ESSAIS, constantes
pipeline.py          # orchestration : ordre des agents, boucle de correction
main.py              # point d'entree CLI
agents/
  base.py            # appeler_agent() : seul acces a Ollama
  entites.py         # agent 1 : entites et domaines
  variables.py       # agent 2 : variables booleennes
  regles.py          # agent 3 : contraintes logiques
  juge.py            # agent 4 : la formalisation correspond-elle a l'enonce ?
  interprete.py      # agent 5 : solution SAT -> reponse en francais
sat/
  syntaxe.py         # validation syntaxique du JSON (deterministe)
  compilation.py     # JSON -> CNF (IDPool, CardEnc)
  solveur.py         # resolution pysat (Glucose), export DIMACS
  controle.py        # verifie que la solution respecte chaque contrainte
tests/tests.json     # 12 problemes avec resultat attendu (SAT/UNSAT, solution)
journal/             # un JSON par execution + logs d'evaluation
documentation/       # guide, workflow, prototype de reference
```

## Principes de code

- Un agent = un fichier, une fonction publique, un prompt en constante. Aucun agent n'appelle un autre : seul `pipeline.py` orchestre
- Seul `agents/base.py` importe `ollama`, et seul le paquet `sat/` importe `pysat`
- Tout ce qui est verifiable par code n'est jamais confie a un LLM
- Le schema JSON est fige : tout changement se repercute en meme temps dans `sat/syntaxe.py`, `sat/compilation.py`, `sat/controle.py` et les prompts
- Nommage en francais, snake_case
