import time
from Controller.PID_pico import PIDController
from Controller.IOs_pico import IO_MODBUS, InOut
from Controller.Dados_pico import Dado
from Controller.Lcd_pico_safe import Lcd
from Controller.KY040_pico_safe import KY040
import ujson as json

# Constantes para arquivos
SETPOINT_FILE = "setpoint_list.json"
PID_VALUES_FILE = "pid_values.json"

def save_setpoint_to_file(setpoint_list, filename=SETPOINT_FILE):
    """
    Salva os setpoints de cada canal em um arquivo JSON.
    """
    try:
        with open(filename, "w") as file:
            json.dump(setpoint_list, file)
        print(f"💾 Setpoints salvos em {filename}")
    except Exception as e:
        print(f"❌ Erro ao salvar setpoints: {e}")

def read_setpoint_from_file(filename=SETPOINT_FILE):
    """
    Lê os setpoints de cada canal de um arquivo JSON.
    Se o arquivo não existir, cria um com valores padrão.
    """
    # Valores padrão caso o arquivo não exista
    default_setpoint_list = [50, 50, 50, 50, 50, 50]

    try:
        with open(filename, "r") as file:
            setpoint_list = json.load(file)
        print(f"💾 Setpoints carregados de {filename}")
        return setpoint_list
    except:
        # Se o arquivo não existir, cria um com valores padrão
        print(f"💾 Arquivo {filename} não encontrado. Criando com valores padrão.")
        save_setpoint_to_file(default_setpoint_list, filename)
        return default_setpoint_list

def save_pid_values(kp_list, ki_list, kd_list, filename=PID_VALUES_FILE):
    """
    Salva os valores de Kp, Ki e Kd em um arquivo JSON.
    """
    try:
        # Cria um dicionário com os valores
        pid_values = {
            "kp": kp_list,
            "ki": ki_list,
            "kd": kd_list
        }

        # Salva o dicionário no arquivo JSON
        with open(filename, "w") as file:
            json.dump(pid_values, file)
        print(f"💾 Valores PID salvos em {filename}")
    except Exception as e:
        print(f"❌ Erro ao salvar valores PID: {e}")

def load_pid_values(filename=PID_VALUES_FILE):
    """
    Carrega os valores de Kp, Ki e Kd de um arquivo JSON.
    Se o arquivo não existir, cria um com valores padrão.
    """
    # Valores padrão caso o arquivo não exista
    default_kp = [30.0, 30.0, 30.0, 30.0, 30.0, 30.0]
    default_ki = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    default_kd = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

    try:
        with open(filename, "r") as file:
            pid_values = json.load(file)
        print(f"💾 Valores PID carregados de {filename}")
        return pid_values["kp"], pid_values["ki"], pid_values["kd"]
    except:
        # Se o arquivo não existir, cria um com valores padrão
        print(f"💾 Arquivo {filename} não encontrado. Criando com valores padrão.")
        save_pid_values(default_kp, default_ki, default_kd, filename)
        return default_kp, default_ki, default_kd

def test_mode():
    """Modo de teste sem hardware - demonstra funcionalidades"""
    print("🧪 === MODO TESTE ATIVADO ===")
    print("⚠️  Executando sem hardware físico conectado")
    print("📱 As funcionalidades serão simuladas")
    
    try:
        # Carrega configurações dos arquivos
        setpoint_list = read_setpoint_from_file()
        kp_list, ki_list, kd_list = load_pid_values()

        print("🔧 Inicializando componentes simulados...")
        
        # Inicializa os componentes em modo simulado
        dado = Dado()
        lcd = Lcd(fake_mode=True)  # LCD simulado
        io = IO_MODBUS(dado=dado)   # UART simulado (fake_modbus=True por padrão)
        pot = KY040(val_min=1, val_max=2, fake_mode=True)  # Encoder simulado
        
        pid = PIDController(
            setpoint_list=setpoint_list, 
            io_modbus=io, 
            kp_list=kp_list, 
            ki_list=ki_list, 
            kd_list=kd_list, 
            adr=[1, 2, 3, 4, 5, 6]
        )
        
        print("🚀 Iniciando controle PID...")
        pid.start(interval=2)  # Intervalo maior para teste

        # Configuração inicial do potenciômetro
        pot.set_counter(1)
        pot.set_limits(1, 2)

        print("✅ Sistema inicializado. Executando simulação por 30 segundos...")
        
        # Simula execução por 30 segundos
        test_duration = 30
        start_time = time.ticks_ms()
        last_pid_update = time.ticks_ms()
        
        while time.ticks_diff(time.ticks_ms(), start_time) < test_duration * 1000:
            try:
                # Executa controle PID manual se não estiver usando thread
                current_time = time.ticks_ms()
                if not hasattr(pid, '_use_thread') or not pid._use_thread:
                    if time.ticks_diff(current_time, last_pid_update) >= 2000:  # 2 segundos
                        pid.control_step()
                        last_pid_update = current_time
                # Simula tela inicial
                if dado.telas == dado.TELA_INICIAL:
                    lcd.lcd_display_string("**** QUALIFIX **** ", 1, 1)
                    lcd.lcd_display_string("Iniciar", 2, 1)
                    lcd.lcd_display_string("Configuracoes", 3, 1)
                    
                    # Simula seleção automática
                    elapsed = time.ticks_diff(time.ticks_ms(), start_time) // 1000
                    if elapsed < 10:
                        lcd.lcd_display_string(">", 2, 0)
                        lcd.lcd_display_string(" ", 3, 0)
                    else:
                        lcd.lcd_display_string(">", 3, 0)
                        lcd.lcd_display_string(" ", 2, 0)
                    
                    # Simula entrada na execução após 5 segundos
                    if elapsed == 5:
                        print("🎮 Simulando: Iniciando execução...")
                        lcd.lcd_clear()
                        lcd.lcd_display_string("**** AGUARDE ****  ", 1, 1)
                        dado.set_telas(dado.TELA_EXECUCAO)
                        pid.set_control_flag(True)
                        lcd.lcd_clear()
                    
                    # Simula entrada na configuração após 15 segundos
                    elif elapsed == 15:
                        print("🎮 Simulando: Entrando nas configurações...")
                        pot.set_counter(1)
                        dado.set_telas(dado.TELA_CONFIGURACAO)
                        lcd.lcd_clear()

                elif dado.telas == dado.TELA_EXECUCAO:
                    # Mostra temperaturas simuladas - com tratamento de erro
                    try:
                        lcd.lcd_display_string("Execucao          ", 1, 1)
                        
                        # Converte temperaturas para string de forma segura
                        temp1 = float(pid.value_temp[0]) if pid.value_temp[0] is not None else 0.0
                        temp4 = float(pid.value_temp[3]) if pid.value_temp[3] is not None else 0.0
                        temp2 = float(pid.value_temp[1]) if pid.value_temp[1] is not None else 0.0
                        temp5 = float(pid.value_temp[4]) if pid.value_temp[4] is not None else 0.0
                        temp3 = float(pid.value_temp[2]) if pid.value_temp[2] is not None else 0.0
                        temp6 = float(pid.value_temp[5]) if pid.value_temp[5] is not None else 0.0
                        
                        linha2 = "1:{:.1f} 4:{:.1f}".format(temp1, temp4)
                        linha3 = "2:{:.1f} 5:{:.1f}".format(temp2, temp5)
                        linha4 = "3:{:.1f} 6:{:.1f}".format(temp3, temp6)
                        
                        lcd.lcd_display_string(linha2, 2, 1)
                        lcd.lcd_display_string(linha3, 3, 1)
                        lcd.lcd_display_string(linha4, 4, 1)
                        
                    except Exception as e:
                        print(f"❌ Erro ao exibir temperaturas: {e}")
                        lcd.lcd_display_string("Erro temperaturas", 2, 1)

                    # Simula saída da execução após 10 segundos
                    elapsed = time.ticks_diff(time.ticks_ms(), start_time) // 1000
                    if elapsed == 10:
                        print("🎮 Simulando: Saindo da execução...")
                        lcd.lcd_clear()
                        lcd.lcd_display_string("**** AGUARDE ****  ", 1, 1)
                        io.io_rpi.aciona_maquina_pronta(False)
                        dado.set_telas(dado.TELA_INICIAL)
                        pid.set_control_flag(False)
                        lcd.lcd_clear()
                        pot.set_counter(1)

                elif dado.telas == dado.TELA_CONFIGURACAO:
                    pot.set_limits(1, 3)
                    lcd.lcd_display_string("Configurar:", 1, 1)
                    lcd.lcd_display_string("Temp", 2, 1)
                    lcd.lcd_display_string("PID", 3, 1)
                    lcd.lcd_display_string("Sair", 4, 1)
                    
                    # Simula navegação no menu
                    elapsed = time.ticks_diff(time.ticks_ms(), start_time) // 1000
                    menu_pos = ((elapsed - 15) // 3) % 3 + 1  # Muda a cada 3 segundos
                    
                    if menu_pos == 1:
                        lcd.lcd_display_string(">", 2, 0)
                        lcd.lcd_display_string(" ", 3, 0)
                        lcd.lcd_display_string(" ", 4, 0)
                    elif menu_pos == 2:
                        lcd.lcd_display_string(" ", 2, 0)
                        lcd.lcd_display_string(">", 3, 0)
                        lcd.lcd_display_string(" ", 4, 0)
                    elif menu_pos == 3:
                        lcd.lcd_display_string(" ", 2, 0)
                        lcd.lcd_display_string(" ", 3, 0)
                        lcd.lcd_display_string(">", 4, 0)
                    
                    # Simula saída após 25 segundos
                    if elapsed == 25:
                        print("🎮 Simulando: Saindo das configurações...")
                        dado.set_telas(dado.TELA_INICIAL)
                        lcd.lcd_clear()
                        pot.set_counter(1)

                # Pequeno delay para evitar sobrecarga do processador
                time.sleep_ms(500)  # 500ms para simulação
                
            except Exception as e:
                print(f"❌ Erro no loop de simulação: {e}")
                time.sleep_ms(1000)  # Pausa em caso de erro

        print("⏰ Simulação concluída!")
        
    except Exception as e:
        print(f"❌ Erro crítico na simulação: {e}")
    finally:
        # Cleanup
        try:
            print("🧹 Executando cleanup...")
            lcd.lcd_clear()
            pot.cleanup()
            io.io_rpi.cleanup()
            pid.set_control_flag(False)
            pid.stop()
            print("✅ Cleanup concluído. Sistema encerrado.")
        except Exception as e:
            print(f"❌ Erro durante cleanup: {e}")

def main():
    """Função principal do programa"""
    print("🚀 Iniciando Controle PID no Raspberry Pi Pico 2...")
    
    # Verifica se deve executar em modo teste
    try:
        # Tenta detectar se há hardware conectado
        from machine import I2C, Pin
        i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=100000)
        devices = i2c.scan()
        
        if not devices:
            print("⚠️  Nenhum dispositivo I2C detectado")
            print("🧪 Ativando modo teste sem hardware")
            test_mode()
            return
            
    except Exception as e:
        print(f"⚠️  Erro ao detectar hardware: {e}")
        print("🧪 Ativando modo teste sem hardware")
        test_mode()
        return
    
    # Modo normal com hardware
    print("✅ Hardware detectado - executando modo normal")
    
    try:
        # Carrega configurações dos arquivos
        setpoint_list = read_setpoint_from_file()
        kp_list, ki_list, kd_list = load_pid_values()

        print("🔧 Inicializando componentes...")
        
        # Inicializa os componentes
        dado = Dado()
        lcd = Lcd()
        io = IO_MODBUS(dado=dado)
        pot = KY040(val_min=1, val_max=2)
        
        pid = PIDController(
            setpoint_list=setpoint_list, 
            io_modbus=io, 
            kp_list=kp_list, 
            ki_list=ki_list, 
            kd_list=kd_list, 
            adr=[1, 2, 3, 4, 5, 6]
        )
        
        print("🚀 Iniciando controle PID...")
        pid.start(interval=1)

        # Constantes para telas adicionais
        TELA_CONFIGURACAO_PID = 3
        TELA_CONFIGURACAO_TEMP = 4

        # Configuração inicial do potenciômetro
        pot.set_counter(1)
        pot.set_limits(1, 2)

        print("✅ Sistema inicializado. Entrando no loop principal...")
        
        # [RESTO DO CÓDIGO ORIGINAL - loop principal completo]
        # ... (código do loop principal permanece igual)
        
    except KeyboardInterrupt:
        print("\n⏹️  Encerrando programa...")
    except Exception as e:
        print(f"❌ Erro crítico: {e}")
    finally:
        # Cleanup
        try:
            print("🧹 Executando cleanup...")
            if 'lcd' in locals():
                lcd.lcd_clear()
            if 'pot' in locals():
                pot.cleanup()
            if 'io' in locals():
                io.io_rpi.cleanup()
            if 'pid' in locals():
                pid.set_control_flag(False)
                pid.stop()
            print("✅ Cleanup concluído. Sistema encerrado.")
        except Exception as e:
            print(f"❌ Erro durante cleanup: {e}")

if __name__ == "__main__":
    main()