"""
Suche nach Conversations Methoden mit Context-Support
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
print("🔍 Suche nach Conversation Methoden mit Context")
print("="*80 + "\n")

# Alle Methoden in conversations
conversations = client.conversational_ai.conversations
methods = [m for m in dir(conversations) if not m.startswith('_')]

print(f"📋 Verfügbare Methoden ({len(methods)}):")
for method in methods:
    print(f"   • {method}")

print("\n" + "="*80)
print("🔬 Inspiziere interessante Methoden")
print("="*80)

interesting_methods = ['create', 'get_signed_url', 'get_webrtc_token', 'audio']

for method_name in interesting_methods:
    if hasattr(conversations, method_name):
        print(f"\n📌 {method_name}()")
        print("-" * 80)
        
        method = getattr(conversations, method_name)
        
        try:
            sig = inspect.signature(method)
            print(f"Signature: {sig}")
            
            # Parameter Details
            for param_name, param in sig.parameters.items():
                annotation = param.annotation if param.annotation != inspect.Parameter.empty else 'Any'
                default = param.default if param.default != inspect.Parameter.empty else 'Required'
                print(f"  • {param_name}: {annotation} = {default}")
                
        except Exception as e:
            print(f"  ⚠️  Signature nicht verfügbar: {e}")
        
        # Docstring
        if hasattr(method, '__doc__') and method.__doc__:
            doc_lines = method.__doc__.strip().split('\n')[:5]  # Erste 5 Zeilen
            print(f"\nDocstring (preview):")
            for line in doc_lines:
                print(f"  {line}")

print("\n" + "="*80)

