"""
Inspiziere get_signed_url() vollständig
"""
import sys
import io
import inspect
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
print("🔍 Inspiziere get_signed_url() Methode")
print("="*80 + "\n")

# Hole die Methode
method = client.conversational_ai.conversations.get_signed_url

print("📋 Method Info:")
print(f"   Name: {method.__name__ if hasattr(method, '__name__') else 'N/A'}")
print(f"   Type: {type(method)}")

# Versuche Signature zu bekommen
try:
    sig = inspect.signature(method)
    print(f"\n✅ Signature gefunden:")
    print(f"   {sig}")
    
    print(f"\n📊 Parameter Details:")
    for param_name, param in sig.parameters.items():
        print(f"   • {param_name}:")
        print(f"     - Type: {param.annotation if param.annotation != inspect.Parameter.empty else 'Any'}")
        print(f"     - Default: {param.default if param.default != inspect.Parameter.empty else 'Required'}")
        print(f"     - Kind: {param.kind}")
        
except Exception as e:
    print(f"⚠️  Signature nicht verfügbar: {e}")

# Versuche __doc__ zu lesen
if hasattr(method, '__doc__') and method.__doc__:
    print(f"\n📖 Docstring:")
    print(method.__doc__)

# Versuche dir() für alle Attribute
print(f"\n🔧 Verfügbare Attribute:")
attrs = [a for a in dir(method) if not a.startswith('_')]
for attr in attrs[:20]:
    print(f"   • {attr}")

# Teste mit verschiedenen Parametern
print("\n" + "="*80)
print("🧪 TESTE VERSCHIEDENE PARAMETER")
print("="*80 + "\n")

test_cases = [
    {"agent_id": Config.ELEVENLABS_AGENT_ID},
    {"agent_id": Config.ELEVENLABS_AGENT_ID, "context": {"test": "value"}},
    {"agent_id": Config.ELEVENLABS_AGENT_ID, "context": "test string"},
]

for i, params in enumerate(test_cases, 1):
    print(f"\n🧪 Test {i}: {list(params.keys())}")
    try:
        result = client.conversational_ai.conversations.get_signed_url(**params)
        print(f"   ✅ Erfolg! Result type: {type(result)}")
        if hasattr(result, 'signed_url'):
            print(f"   📝 Signed URL: {result.signed_url[:60]}...")
    except TypeError as e:
        print(f"   ❌ TypeError: {e}")
    except Exception as e:
        print(f"   ❌ Error: {type(e).__name__}: {e}")

print("\n" + "="*80)

