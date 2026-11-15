



MODELE_ENTITES = "qwen3.5:4b"
MODELE_VARIABLES = "qwen3.5:4b"
MODELE_REGLES = "qwen3.5:9b-U"
MODELE_JUGE = "deepseek-r1:8b"
MODELE_INTERPRETE = "qwen3.5:4b"

OPTIONS = {"num_ctx": 16384, "temperature": 0.2, "num_predict": -1}

MAX_ESSAIS = 3

TYPES_CONTRAINTES = {"clause", "au_moins_un", "au_plus_un", "exactement_un",
                     "implique", "pas_tous"}

DOSSIER_JOURNAL = "journal"
FICHIER_CNF = "probleme.cnf"
