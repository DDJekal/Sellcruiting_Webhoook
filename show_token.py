"""
Zeige geladenen Token
"""
from config import Config

token = Config.HIRINGS_API_TOKEN

print(f"Aktuell geladener Token:")
print(f"{token}")
print(f"\nLänge: {len(token)} Zeichen")
print(f"\nErste 50: {token[:50]}")
print(f"Letzte 50: {token[-50:]}")

