#!/usr/bin/env python3
"""
Simple test for emotional system without full bot dependencies.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("🧪 SIMPLE EMOTIONAL SYSTEM TEST")
print("=" * 40)

# Test 1: Check if emotional services were created
print("📁 Checking emotional service files...")

files_to_check = [
    "services/emotional_analysis_service.py",
    "services/character_voice_service.py", 
    "database/emotional_models.py"
]

for file_path in files_to_check:
    if os.path.exists(file_path):
        print(f"   ✅ {file_path} - EXISTS")
        # Check file size to verify it's not empty
        size = os.path.getsize(file_path)
        print(f"      Size: {size} bytes")
    else:
        print(f"   ❌ {file_path} - MISSING")

print()

# Test 2: Check coordinador_central integration
print("🔗 Checking CoordinadorCentral integration...")

try:
    with open("services/coordinador_central.py", "r") as f:
        content = f.read()
        
    if "EmotionalAnalysisService" in content:
        print("   ✅ EmotionalAnalysisService import found")
    else:
        print("   ❌ EmotionalAnalysisService import missing")
        
    if "CharacterVoiceService" in content:
        print("   ✅ CharacterVoiceService import found")
    else:
        print("   ❌ CharacterVoiceService import missing")
        
    if "self.emotional_analysis" in content:
        print("   ✅ Emotional analysis initialization found")
    else:
        print("   ❌ Emotional analysis initialization missing")
        
except Exception as e:
    print(f"   ❌ Error reading coordinador_central.py: {str(e)}")

print()

# Test 3: Check handlers integration
print("🎮 Checking handlers integration...")

handlers_with_coordinador = [
    "handlers/reaction_handler.py",
    "handlers/narrative_handlers.py"
]

for handler_path in handlers_with_coordinador:
    if os.path.exists(handler_path):
        try:
            with open(handler_path, "r") as f:
                content = f.read()
            
            if "CoordinadorCentral" in content and "AccionUsuario" in content:
                print(f"   ✅ {handler_path} - Integrated with CoordinadorCentral")
            else:
                print(f"   ⚠️ {handler_path} - Missing CoordinadorCentral integration")
        except:
            print(f"   ❌ {handler_path} - Read error")
    else:
        print(f"   ❌ {handler_path} - File missing")

print()

# Test 4: Check bot.py logs for startup
print("📋 Checking bot startup logs...")

if os.path.exists("bot.log"):
    try:
        # Check last few lines of log for successful startup
        with open("bot.log", "r") as f:
            lines = f.readlines()
            
        recent_lines = lines[-20:] if len(lines) > 20 else lines
        
        for line in recent_lines:
            if "Bot iniciado correctamente" in line:
                print(f"   ✅ Found successful startup: {line.strip()}")
                break
        else:
            print("   ⚠️ No recent successful startup found")
            
        # Check for emotional service errors
        error_count = 0
        for line in recent_lines:
            if "EmotionalAnalysisService" in line and ("error" in line.lower() or "exception" in line.lower()):
                error_count += 1
                
        if error_count == 0:
            print("   ✅ No emotional service errors in recent logs")
        else:
            print(f"   ⚠️ Found {error_count} emotional service errors in recent logs")
            
    except Exception as e:
        print(f"   ❌ Error reading bot.log: {str(e)}")
else:
    print("   ❌ bot.log file not found")

print()
print("🎯 INTEGRATION POINTS AVAILABLE FOR TESTING:")
print("-" * 40)
print("1. 📱 Reaction to publications (ip_channelid_msgid_reaction callbacks)")
print("2. 🎭 Narrative decisions (/start_story command)")  
print("3. 💬 Channel participation (automatic detection)")
print("4. ✨ Daily engagement (/daily or similar commands)")
print()
print("🚀 Bot should be running with emotional analysis integrated!")
print("   Test by interacting with the bot through Telegram")