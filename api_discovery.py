"""
API Discovery: Welche Methoden gibt es für Conversational AI?
"""
import sys
import io
from elevenlabs import ElevenLabs
from config import Config

# Fix Windows Terminal Encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

client = ElevenLabs(api_key=Config.ELEVENLABS_API_KEY)

print("="*70)
print("🔍 ELEVENLABS API EXPLORATION")
print("="*70 + "\n")

print("1️⃣ conversational_ai Methoden:")
conv_ai_methods = [m for m in dir(client.conversational_ai) if not m.startswith('_')]
for method in conv_ai_methods:
    print(f"   • {method}")

print("\n2️⃣ conversational_ai.conversations Methoden:")
conv_methods = [m for m in dir(client.conversational_ai.conversations) if not m.startswith('_')]
for method in conv_methods:
    print(f"   • {method}")

print("\n3️⃣ Versuche verschiedene Methoden:")

# Versuche: create
try:
    print("\n   Teste: conversations.create()...")
    result = client.conversational_ai.conversations.create(
        agent_id=Config.ELEVENLABS_AGENT_ID
    )
    print(f"   ✅ create() funktioniert!")
    print(f"   Typ: {type(result)}")
    print(f"   Attribute: {[a for a in dir(result) if not a.startswith('_')][:10]}")
except Exception as e:
    print(f"   ❌ create() Fehler: {e}")

# Versuche: list
try:
    print("\n   Teste: conversations.list()...")
    result = client.conversational_ai.conversations.list()
    print(f"   ✅ list() funktioniert!")
    print(f"   Typ: {type(result)}")
except Exception as e:
    print(f"   ❌ list() Fehler: {e}")

print("\n" + "="*70)

