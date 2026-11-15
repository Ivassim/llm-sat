import sys

from pipeline import resoudre_probleme

EXEMPLE = """Alice, Bob et Chloé commandent chacun exactement une boisson : thé ou café.
Alice et Bob ne prennent pas la même boisson.
Si Chloé prend du thé, alors Bob prend du café.
Chloé prend du thé.
Qui boit quoi ?"""

if __name__ == "__main__":
    resoudre_probleme(sys.argv[1] if len(sys.argv) > 1 else EXEMPLE)
