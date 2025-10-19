"""
Exemplo de configuração e teste para o Raspberry Pi Pico 2
Este arquivo demonstra como usar os módulos adaptados individualmente
"""

import time
from machine import Pin

def test_ios():
    """Testa o módulo IOs_pico"""
    print("=== Testando IOs ===")
    try:
        from IOs_pico import IO_MODBUS, InOut
        
        # Teste básico do InOut
        print("Inicializando InOut...")
        inout = InOut()
        
        # Testa entrada digital
        print(f"Estado da entrada da máquina: {inout.get_aciona_maquina}")
        
        # Testa PWM
        print("Testando PWM...")
        for canal in range(1, 7):
            print(f"  PWM Canal {canal}: 50%")
            inout.aciona_pwm(50, canal)
            time.sleep(1)
            inout.aciona_pwm(0, canal)
        
        # Testa saída digital
        print("Testando saída máquina pronta...")
        inout.aciona_maquina_pronta(True)   # Liga
        time.sleep(1)
        inout.aciona_maquina_pronta(False)  # Desliga
        
        inout.cleanup()
        print("✅ Teste IOs concluído")
        
    except Exception as e:
        print(f"❌ Erro no teste IOs: {e}")

def test_lcd():
    """Testa o módulo LCD"""
    print("\n=== Testando LCD ===")
    try:
        from Lcd_pico import Lcd
        
        print("Inicializando LCD...")
        lcd = Lcd()
        
        # Testa display básico
        lcd.lcd_clear()
        lcd.lcd_display_string("Pi Pico 2 Test", 1, 1)
        lcd.lcd_display_string("LCD Funcionando!", 2, 1)
        lcd.lcd_display_string("Linha 3", 3, 1)
        lcd.lcd_display_string("Linha 4", 4, 1)
        
        time.sleep(2)
        
        # Testa backlight
        print("Testando backlight...")
        lcd.backlight(0)  # Desliga
        time.sleep(1)
        lcd.backlight(1)  # Liga
        
        # Testa string invertida
        lcd.lcd_display_string_inverter("Invertido!", 2, 1)
        
        time.sleep(2)
        lcd.lcd_clear()
        
        print("✅ Teste LCD concluído")
        
    except Exception as e:
        print(f"❌ Erro no teste LCD: {e}")

def test_encoder():
    """Testa o encoder KY040"""
    print("\n=== Testando Encoder KY040 ===")
    try:
        from KY040_pico import KY040
        
        print("Inicializando KY040...")
        encoder = KY040(val_min=0, val_max=100)
        
        print("Gire o encoder ou pressione o botão por 10 segundos...")
        print("(Counter inicial:", encoder.get_counter(), ")")
        
        last_counter = encoder.get_counter()
        last_sw = encoder.get_sw_status
        
        for i in range(100):  # 10 segundos
            current_counter = encoder.get_counter()
            current_sw = encoder.get_sw_status
            
            if current_counter != last_counter:
                print(f"Counter: {current_counter}")
                last_counter = current_counter
                
            if current_sw != last_sw:
                print(f"Botão: {'Pressionado' if current_sw == 0 else 'Liberado'}")
                last_sw = current_sw
                
            time.sleep_ms(100)
        
        encoder.cleanup()
        print("✅ Teste Encoder concluído")
        
    except Exception as e:
        print(f"❌ Erro no teste Encoder: {e}")

def test_pid():
    """Testa o controlador PID"""
    print("\n=== Testando PID Controller ===")
    try:
        from PID_pico import PIDController
        from IOs_pico import IO_MODBUS
        
        print("Inicializando PID...")
        io_modbus = IO_MODBUS()
        
        pid = PIDController(
            kp_list=[1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
            ki_list=[0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
            kd_list=[0.05, 0.05, 0.05, 0.05, 0.05, 0.05],
            setpoint_list=[100, 100, 100, 100, 100, 100],
            io_modbus=io_modbus,
            adr=[1, 2, 3, 4, 5, 6]
        )
        
        print("Iniciando controle PID...")
        pid.start(interval=1)
        
        print("Ativando controle...")
        pid.set_control_flag(True)
        
        # Monitora por 10 segundos
        for i in range(10):
            status = pid.get_status()
            print(f"Segundo {i+1} - Temps: {[f'{t:.1f}' for t in status['temperatures']]}")
            time.sleep(1)
        
        print("Desativando controle...")
        pid.set_control_flag(False)
        pid.stop()
        
        print("✅ Teste PID concluído")
        
    except Exception as e:
        print(f"❌ Erro no teste PID: {e}")

def test_file_system():
    """Testa o sistema de arquivos"""
    print("\n=== Testando Sistema de Arquivos ===")
    try:
        import ujson as json
        
        # Teste de escrita
        test_data = {
            "setpoints": [50, 60, 70, 80, 90, 100],
            "kp": [1.0, 1.1, 1.2, 1.3, 1.4, 1.5],
            "ki": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
            "kd": [0.05, 0.06, 0.07, 0.08, 0.09, 0.1]
        }
        
        print("Salvando arquivo de teste...")
        with open("test_config.json", "w") as f:
            json.dump(test_data, f)
        
        print("Carregando arquivo de teste...")
        with open("test_config.json", "r") as f:
            loaded_data = json.load(f)
        
        print("Dados carregados:", loaded_data)
        
        # Verifica se os dados são iguais
        if test_data == loaded_data:
            print("✅ Teste Sistema de Arquivos concluído")
        else:
            print("❌ Dados não conferem!")
            
    except Exception as e:
        print(f"❌ Erro no teste Sistema de Arquivos: {e}")

def main():
    """Executa todos os testes"""
    print("🚀 INICIANDO TESTES DO RASPBERRY PI PICO 2")
    print("=" * 50)
    
    # Lista de testes disponíveis
    tests = [
        ("IOs (GPIO/PWM/UART)", test_ios),
        ("LCD I2C", test_lcd), 
        ("Encoder KY040", test_encoder),
        ("PID Controller", test_pid),
        ("Sistema de Arquivos", test_file_system)
    ]
    
    print("Testes disponíveis:")
    for i, (name, _) in enumerate(tests):
        print(f"  {i+1}. {name}")
    print("  0. Executar todos")
    
    try:
        choice = int(input("Escolha um teste (0-5): "))
        
        if choice == 0:
            # Executa todos os testes
            for name, test_func in tests:
                print(f"\n🔄 Executando: {name}")
                test_func()
        elif 1 <= choice <= len(tests):
            # Executa teste específico
            name, test_func = tests[choice - 1]
            print(f"\n🔄 Executando: {name}")
            test_func()
        else:
            print("❌ Opção inválida!")
            
    except KeyboardInterrupt:
        print("\n⏹️ Testes interrompidos pelo usuário")
    except Exception as e:
        print(f"❌ Erro geral: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 TESTES FINALIZADOS")

if __name__ == "__main__":
    main()