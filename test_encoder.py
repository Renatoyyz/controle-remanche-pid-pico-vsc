"""
Teste Individual - Encoder Rotativo KY040
Raspberry Pi Pico - CLK=GP14, DT=GP15, SW=GP16
"""

from Controller.KY040_pico import KY040
import time

print("=" * 50)
print("TESTE ENCODER ROTATIVO KY040")
print("=" * 50)
print()
print("Configuração:")
print("  - CLK (Clock): GPIO 14")
print("  - DT (Data):   GPIO 15")
print("  - SW (Switch): GPIO 16")
print()
print("Instruções:")
print("  1. Gire o encoder no sentido horário")
print("  2. Gire o encoder no sentido anti-horário")
print("  3. Pressione o botão do encoder")
print("  4. Pressione Ctrl+C para sair")
print()
print("-" * 50)

try:
    print("Inicializando encoder...")
    # Criar encoder com range de 1 a 100
    encoder = KY040(clk_pin=14, dt_pin=15, sw_pin=16, val_min=1, val_max=100)
    encoder.set_counter(50)  # Valor inicial no meio
    print("✅ Encoder inicializado com sucesso!")
    print()
    
    last_value = encoder.get_counter()
    last_sw = encoder.sw_status
    
    print("Aguardando interações... (valor inicial: {})".format(last_value))
    print()
    
    while True:
        current_value = encoder.get_counter()
        current_sw = encoder.sw_status
        
        # Detecta mudança no valor
        if current_value != last_value:
            if current_value > last_value:
                direction = "HORÁRIO ➡️"
            else:
                direction = "⬅️ ANTI-HORÁRIO"
            
            print("Encoder: {} | Valor: {} | {}".format(
                direction, current_value, 
                "#" * (current_value // 5)  # Barra de progresso
            ))
            last_value = current_value
        
        # Detecta pressão do botão (ativo baixo: 0 = pressionado)
        if current_sw == 0 and last_sw == 1:
            print()
            print("🔘 BOTÃO PRESSIONADO! (Valor atual: {})".format(current_value))
            print()
        
        last_sw = current_sw
        time.sleep_ms(50)  # Pequeno delay para evitar leituras excessivas
        
except KeyboardInterrupt:
    print()
    print()
    print("✅ Teste interrompido pelo usuário.")
    print("Valor final do encoder: {}".format(encoder.get_counter()))
    
except Exception as e:
    print()
    print(f"❌ Erro no teste do encoder: {e}")
    import sys
    sys.print_exception(e)
    
print()
print("Teste finalizado.")
print("=" * 50)