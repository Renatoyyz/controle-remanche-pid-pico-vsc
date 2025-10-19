"""
Teste Individual - LCD I2C 20x4
Raspberry Pi Pico - GPIO 8 (SDA) e GPIO 9 (SCL)
"""

from Controller.Lcd_pico import Lcd
import time

print("=" * 50)
print("TESTE LCD I2C 20x4")
print("=" * 50)
print()
print("Configuração:")
print("  - I2C0: SDA=GP8, SCL=GP9")
print("  - Endereço: 0x27 ou 0x3F (auto-detectado)")
print()

try:
    print("Inicializando LCD...")
    lcd = Lcd()
    print("✅ LCD inicializado com sucesso!")
    print()
    
    # Teste 1: Linhas individuais
    print("Teste 1: Escrevendo em cada linha...")
    lcd.lcd_clear()
    lcd.lcd_display_string("*** TESTE LCD ***", 1, 1)
    time.sleep(1)
    lcd.lcd_display_string("Linha 2 - OK", 2, 1)
    time.sleep(1)
    lcd.lcd_display_string("Linha 3 - OK", 3, 1)
    time.sleep(1)
    lcd.lcd_display_string("Linha 4 - OK", 4, 1)
    time.sleep(2)
    
    # Teste 2: Posicionamento
    print("Teste 2: Testando posicionamento...")
    lcd.lcd_clear()
    lcd.lcd_display_string("Pos 0,0", 1, 0)
    lcd.lcd_display_string("Pos 5,1", 2, 5)
    lcd.lcd_display_string("Pos 10,2", 3, 10)
    lcd.lcd_display_string("Pos 15,3", 4, 15)
    time.sleep(2)
    
    # Teste 3: Caracteres especiais
    print("Teste 3: Caracteres especiais...")
    lcd.lcd_clear()
    lcd.lcd_display_string("Temp: 25.5", 1, 1)
    lcd.lcd_display_string("Kp:1.00 Ki:0.10", 2, 1)
    lcd.lcd_display_string("Kd:0.05", 3, 1)
    lcd.lcd_display_string("Status: OK!", 4, 1)
    time.sleep(2)
    
    # Teste 4: Clear e mensagem final
    print("Teste 4: Limpeza de tela...")
    lcd.lcd_clear()
    lcd.lcd_display_string("TESTE COMPLETO!", 2, 2)
    time.sleep(2)
    
    lcd.lcd_clear()
    print()
    print("✅ Todos os testes do LCD passaram!")
    
except Exception as e:
    print(f"❌ Erro no teste do LCD: {e}")
    import sys
    sys.print_exception(e)
    
print()
print("Teste finalizado.")
print("=" * 50)