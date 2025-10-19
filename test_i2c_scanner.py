"""
Scanner I2C - Detecta dispositivos conectados
Raspberry Pi Pico - I2C0: SDA=GP8, SCL=GP9
"""

from machine import I2C, Pin
import time

print("=" * 50)
print("SCANNER I2C")
print("=" * 50)
print()
print("Configuração:")
print("  - I2C0: SDA=GPIO 8, SCL=GPIO 9")
print("  - Frequência: 400kHz")
print()
print("Procurando dispositivos I2C...")
print("-" * 50)

try:
    # Inicializa I2C0
    i2c = I2C(0, scl=Pin(9), sda=Pin(8), freq=400000)
    
    print()
    print("I2C inicializado com sucesso!")
    print()
    
    # Escaneia o barramento I2C
    devices = i2c.scan()
    
    if devices:
        print("✅ {} dispositivo(s) encontrado(s):".format(len(devices)))
        print()
        
        for device in devices:
            print("  • Endereço: 0x{:02X} (decimal: {})".format(device, device))
            
            # Identifica dispositivos comuns
            if device == 0x27:
                print("    ℹ️  Provável: LCD 20x4 I2C (endereço padrão 0x27)")
            elif device == 0x3F:
                print("    ℹ️  Provável: LCD 20x4 I2C (endereço alternativo 0x3F)")
            elif device in [0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26]:
                print("    ℹ️  Provável: Expansor I/O PCF8574")
            elif device in [0x48, 0x49, 0x4A, 0x4B]:
                print("    ℹ️  Provável: Conversor ADC ADS1115")
            elif device == 0x68:
                print("    ℹ️  Provável: RTC DS1307/DS3231 ou IMU MPU6050")
            elif device == 0x76 or device == 0x77:
                print("    ℹ️  Provável: Sensor BME280/BMP280")
        
        print()
        print("-" * 50)
        print()
        print("INSTRUÇÕES:")
        print("  1. Anote o endereço hexadecimal do LCD")
        print("  2. Se for 0x27 ou 0x3F, o código já suporta")
        print("  3. Se for outro endereço, ajuste no código")
        
    else:
        print("❌ Nenhum dispositivo I2C encontrado!")
        print()
        print("Possíveis causas:")
        print("  1. LCD não conectado")
        print("  2. Cabos SDA/SCL invertidos")
        print("  3. Alimentação do LCD desligada")
        print("  4. Pinos GPIO incorretos")
        print("  5. LCD com defeito")
        print()
        print("Verifique:")
        print("  • SDA → GPIO 8 (Pin 11)")
        print("  • SCL → GPIO 9 (Pin 12)")
        print("  • VCC → 5V ou 3.3V")
        print("  • GND → GND")
    
    print()
    
    # Teste adicional: leitura de dados
    if devices:
        print("Tentando ler dados dos dispositivos...")
        print()
        
        for device in devices:
            try:
                # Tenta ler 1 byte
                data = i2c.readfrom(device, 1)
                print("  0x{:02X}: Leitura OK - Dados: {}".format(device, data.hex()))
            except:
                print("  0x{:02X}: Não foi possível ler (pode ser normal)".format(device))
        
        print()
    
except Exception as e:
    print()
    print(f"❌ Erro ao escanear I2C: {e}")
    import sys
    sys.print_exception(e)
    
print()
print("=" * 50)
print()
print("MAPA DE PINOS - Raspberry Pi Pico:")
print()
print("  I2C0 SDA → GPIO 8  (Pin 11)")
print("  I2C0 SCL → GPIO 9  (Pin 12)")
print("  I2C1 SDA → GPIO 26 (Pin 31)")
print("  I2C1 SCL → GPIO 27 (Pin 32)")
print()
print("=" * 50)