"""
Inspiziere Conversations API
"""
import sys
import io
from elevenlabs import ElevenLabs
from elevenlabs.environment import ElevenLabsEnvironment
from config import Config

# Fix Windows Terminal Encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

client = ElevenLabs(
    api_key=Config.ELEVENLABS_API_KEY,
    environment=ElevenLabsEnvironment.PRODUCTION_EU
)

print("\n" + "="*80)
print("🔍 Inspiziere Conversations API")
print("="*80 + "\n")

print("1️⃣ Verfügbare Methoden in conversations:")
methods = [m for m in dir(client.conversational_ai.conversations) if not m.startswith('_')]
for method in methods:
    print(f"   • {method}")

print("\n2️⃣ Prüfe ob get_signed_url existiert:")
if hasattr(client.conversational_ai.conversations, 'get_signed_url'):
    import inspect
    sig = inspect.signature(client.conversational_ai.conversations.get_signed_url)
    print(f"   ✅ get_signed_url existiert")
    print(f"   Signatur: {sig}")
else:
    print(f"   ❌ get_signed_url existiert NICHT")

print("\n" + "="*80)

