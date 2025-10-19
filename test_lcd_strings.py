#!/usr/bin/env python3
"""
Teste isolado para verificar o comportamento do LCD com strings formatadas
"""

import sys
import os
sys.path.append('/Volumes/RenatoDados/Projetos/controle-remanche-pid-pico-vsc')

from Controller.Lcd_pico_safe import LcdPico

# Cria instância do LCD (vai usar FakeLcd automaticamente)
lcd = LcdPico()

print("🧪 Testando diferentes tipos de entrada no LCD:")

# Teste 1: Strings literais (devem funcionar)
try:
    lcd.lcd_display_string("Teste literal", 1, 1)
    print("✅ String literal OK")
except Exception as e:
    print(f"❌ String literal falhou: {e}")

# Teste 2: Strings formatadas com .format()
try:
    temp1, temp4 = 25.5, 30.2
    linha2 = "1:{:.1f} 4:{:.1f}".format(temp1, temp4)
    lcd.lcd_display_string(linha2, 2, 1)
    print(f"✅ String formatada OK: '{linha2}'")
except Exception as e:
    print(f"❌ String formatada falhou: {e}")

# Teste 3: Números diretos
try:
    lcd.lcd_display_string(123, 3, 1)
    print("✅ Número inteiro OK")
except Exception as e:
    print(f"❌ Número inteiro falhou: {e}")

# Teste 4: Float direto
try:
    lcd.lcd_display_string(25.5, 4, 1)
    print("✅ Float OK")
except Exception as e:
    print(f"❌ Float falhou: {e}")

# Teste 5: None (deve ser tratado)
try:
    lcd.lcd_display_string(None, 1, 1)
    print("✅ None OK")
except Exception as e:
    print(f"❌ None falhou: {e}")

print("\n🔍 Estado final do buffer LCD:")
for i, linha in enumerate(lcd.display_buffer, 1):
    print(f"Linha {i}: '{linha}'")