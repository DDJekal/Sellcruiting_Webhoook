"""
Inspiziere SIP Trunk outbound_call() Parameter
"""
import sys
import io
from elevenlabs import ElevenLabs
from elevenlabs.environment import ElevenLabsEnvironment
from config import Config
import inspect

# Fix Windows Terminal Encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

client = ElevenLabs(
    api_key=Config.ELEVENLABS_API_KEY,
    environment=ElevenLabsEnvironment.PRODUCTION_EU
)

print("\n" + "="*80)
print("🔍 SIP Trunk outbound_call() Parameter-Inspektion")
print("="*80 + "\n")

# 1. Signatur
sig = inspect.signature(client.conversational_ai.sip_trunk.outbound_call)
print("1️⃣ Funktions-Signatur:")
print(f"   {sig}\n")

# 2. Parameter-Details
print("2️⃣ Parameter-Details:")
for param_name, param in sig.parameters.items():
    default = param.default if param.default != inspect.Parameter.empty else "REQUIRED"
    annotation = param.annotation if param.annotation != inspect.Parameter.empty else "any"
    print(f"   • {param_name}: {annotation}")
    print(f"     Default: {default}")

# 3. Docstring
print("\n3️⃣ Docstring:")
docstring = client.conversational_ai.sip_trunk.outbound_call.__doc__
if docstring:
    print(docstring[:500])
else:
    print("   (Kein Docstring verfügbar)")

print("\n" + "="*80)

