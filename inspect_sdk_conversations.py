"""
Inspiziere ElevenLabs SDK: Conversational AI Methods
"""
from elevenlabs import ElevenLabs
from elevenlabs.environment import ElevenLabsEnvironment
from config import Config

client = ElevenLabs(
    api_key=Config.ELEVENLABS_API_KEY,
    environment=ElevenLabsEnvironment.PRODUCTION_EU
)

print("\n" + "="*70)
print("🔍 ELEVENLABS SDK: Conversational AI Methods")
print("="*70)

print("\n1. conversational_ai Client:")
print(dir(client.conversational_ai))

print("\n2. Agents Methods:")
if hasattr(client.conversational_ai, 'agents'):
    print(dir(client.conversational_ai.agents))

print("\n3. Conversations Methods:")
if hasattr(client.conversational_ai, 'conversations'):
    print(dir(client.conversational_ai.conversations))

print("\n4. SIP Trunk Methods:")
if hasattr(client.conversational_ai, 'sip_trunk'):
    print(dir(client.conversational_ai.sip_trunk))

print("\n" + "="*70)

