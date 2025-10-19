"""
Teste Individual - Comunicação UART/Modbus
Raspberry Pi Pico - TX=GP0, RX=GP1
"""

from Controller.IOs_pico import IO_MODBUS
import time

print("=" * 50)
print("TESTE UART/MODBUS RTU")
print("=" * 50)
print()
print("Configuração:")
print("  - UART0: TX=GP0, RX=GP1")
print("  - Baudrate: 9600")
print("  - Protocolo: Modbus RTU")
print()
print("Conecte os sensores de temperatura Modbus")
print("nos endereços: 1, 2, 3, 4, 5, 6")
print()
print("-" * 50)

try:
    print("Inicializando UART/Modbus...")
    # Endereços dos dispositivos Modbus (ajuste conforme sua configuração)
    enderecos = [1, 2, 3, 4, 5, 6]
    
    # Inicializa o sistema de I/O Modbus
    io_modbus = IO_MODBUS(
        dado=None,
        uart_id=0,
        tx_pin=0,
        rx_pin=1,
        baudrate=9600
    )
    
    print("✅ UART/Modbus inicializado!")
    print()
    
    # Teste 1: Leitura de temperaturas
    print("Teste 1: Leitura de temperaturas...")
    print("-" * 50)
    
    for tentativa in range(3):
        print()
        print("Tentativa {} de 3:".format(tentativa + 1))
        print()
        
        for i, endereco in enumerate(enderecos):
            try:
                print("  Lendo canal {} (endereço {})...".format(i+1, endereco), end=" ")
                temperatura = io_modbus.get_temperature_channel(endereco)
                
                if temperatura is not None and temperatura > 0:
                    print("✅ {:.1f}°C".format(temperatura))
                else:
                    print("⚠️  Sem resposta")
                    
                time.sleep_ms(100)  # Pequeno delay entre leituras
                
            except Exception as e:
                print("❌ Erro: {}".format(e))
        
        if tentativa < 2:
            print()
            print("Aguardando 2 segundos...")
            time.sleep(2)
    
    print()
    print("-" * 50)
    print()
    
    # Teste 2: Leitura contínua (15 segundos)
    print("Teste 2: Monitoramento contínuo (15 segundos)")
    print("Pressione Ctrl+C para interromper")
    print("-" * 50)
    
    start_time = time.time()
    leitura_count = 0
    
    while time.time() - start_time < 15:
        leitura_count += 1
        print()
        print("Leitura #{}:".format(leitura_count))
        
        temps = []
        for i, endereco in enumerate(enderecos):
            try:
                temp = io_modbus.get_temperature_channel(endereco)
                if temp is not None:
                    temps.append(temp)
                    print("  Canal {}: {:.1f}°C".format(i+1, temp))
                else:
                    print("  Canal {}: ---".format(i+1))
            except:
                print("  Canal {}: ERRO".format(i+1))
        
        if temps:
            media = sum(temps) / len(temps)
            print("  Média: {:.1f}°C".format(media))
        
        time.sleep(2)
    
    print()
    print("✅ Teste de leitura contínua concluído!")
    
except KeyboardInterrupt:
    print()
    print()
    print("✅ Teste interrompido pelo usuário.")
    
except Exception as e:
    print()
    print(f"❌ Erro no teste UART/Modbus: {e}")
    import sys
    sys.print_exception(e)
    
print()
print("Teste finalizado.")
print("=" * 50)
print()
print("NOTAS:")
print("  - Se nenhuma temperatura foi lida, verifique:")
print("    1. Cabos TX/RX conectados corretamente")
print("    2. Baudrate correto (9600)")
print("    3. Endereços Modbus dos sensores")
print("    4. Alimentação dos sensores")
print("    5. Terminadores RS485 (se aplicável)")
print("=" * 50)