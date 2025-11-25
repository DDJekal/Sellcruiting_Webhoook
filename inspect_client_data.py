"""
Test: conversation_initiation_client_data Parameter
"""
import sys
import io
from elevenlabs import ElevenLabs
from elevenlabs.environment import ElevenLabsEnvironment
from elevenlabs.types import ConversationInitiationClientDataRequestInput
from config import Config
import inspect

# Fix Windows Terminal Encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

client = ElevenLabs(
    api_key=Config.ELEVENLABS_API_KEY,
    environment=ElevenLabsEnvironment.PRODUCTION_EU
)

print("\n" + "="*80)
print("🔍 Untersuche: ConversationInitiationClientDataRequestInput")
print("="*80 + "\n")

# Versuche die Klasse zu importieren und inspizieren
try:
    from elevenlabs.types.conversation_initiation_client_data_request_input import ConversationInitiationClientDataRequestInput
    
    print("1️⃣ Klasse erfolgreich importiert!")
    print(f"   Type: {ConversationInitiationClientDataRequestInput}\n")
    
    # Inspiziere die Klasse
    print("2️⃣ Verfügbare Attribute/Methoden:")
    for attr in dir(ConversationInitiationClientDataRequestInput):
        if not attr.startswith('_'):
            print(f"   • {attr}")
    
    # Versuche Init-Signatur zu bekommen
    try:
        init_sig = inspect.signature(ConversationInitiationClientDataRequestInput.__init__)
        print(f"\n3️⃣ __init__ Signatur:")
        print(f"   {init_sig}")
        
        print("\n4️⃣ Parameter-Details:")
        for param_name, param in init_sig.parameters.items():
            if param_name != 'self':
                default = param.default if param.default != inspect.Parameter.empty else "REQUIRED"
                annotation = param.annotation if param.annotation != inspect.Parameter.empty else "any"
                print(f"   • {param_name}: {annotation}")
                print(f"     Default: {default}")
    except Exception as e:
        print(f"\n3️⃣ Konnte __init__ nicht inspizieren: {e}")
    
    # Versuche Docstring
    if ConversationInitiationClientDataRequestInput.__doc__:
        print(f"\n5️⃣ Docstring:")
        print(ConversationInitiationClientDataRequestInput.__doc__)
    
    # Versuche ein Beispiel-Objekt zu erstellen
    print("\n6️⃣ Teste Objekt-Erstellung:")
    print("   Versuche leeres Objekt...")
    try:
        test_obj = ConversationInitiationClientDataRequestInput()
        print(f"   ✅ Leeres Objekt erstellt: {test_obj}")
    except Exception as e:
        print(f"   ⚠️  Fehler bei leerem Objekt: {e}")
    
    print("\n   Versuche mit 'custom_llm_extra_body' Parameter...")
    try:
        test_obj = ConversationInitiationClientDataRequestInput(
            custom_llm_extra_body={"test": "value"}
        )
        print(f"   ✅ Objekt mit custom_llm_extra_body erstellt")
    except Exception as e:
        print(f"   ⚠️  Fehler: {e}")
    
    print("\n   Versuche mit 'variables' Parameter...")
    try:
        test_obj = ConversationInitiationClientDataRequestInput(
            variables={"context": "test", "name": "Max"}
        )
        print(f"   ✅ Objekt mit variables erstellt")
    except Exception as e:
        print(f"   ⚠️  Fehler: {e}")
    
except ImportError as e:
    print(f"❌ Konnte Klasse nicht importieren: {e}")

print("\n" + "="*80)

