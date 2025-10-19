import time
from Controller.PID_pico import PIDController
from Controller.IOs_pico import IO_MODBUS, InOut
from Controller.Dados_pico import Dado
from Controller.Lcd_pico import Lcd
from Controller.KY040_pico import KY040
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
        print(f"Setpoints salvos em {filename}")
    except Exception as e:
        print(f"Erro ao salvar setpoints: {e}")

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
        print(f"Setpoints carregados de {filename}")
        return setpoint_list
    except:
        # Se o arquivo não existir, cria um com valores padrão
        print(f"Arquivo {filename} não encontrado. Criando com valores padrão.")
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
        print(f"Valores PID salvos em {filename}")
    except Exception as e:
        print(f"Erro ao salvar valores PID: {e}")

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
        print(f"Valores PID carregados de {filename}")
        return pid_values["kp"], pid_values["ki"], pid_values["kd"]
    except:
        # Se o arquivo não existir, cria um com valores padrão
        print(f"Arquivo {filename} não encontrado. Criando com valores padrão.")
        save_pid_values(default_kp, default_ki, default_kd, filename)
        return default_kp, default_ki, default_kd

def main():
    """Função principal do programa"""
    print("Iniciando Controle PID no Raspberry Pi Pico 2...")
    
    try:
        # Carrega configurações dos arquivos
        setpoint_list = read_setpoint_from_file()
        kp_list, ki_list, kd_list = load_pid_values()

        print("Inicializando componentes...")
        
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
        
        print("Iniciando controle PID...")
        pid.start(interval=1)

        # Constantes para telas adicionais
        TELA_CONFIGURACAO_PID = 3
        TELA_CONFIGURACAO_TEMP = 4

        # Configuração inicial do potenciômetro
        pot.set_counter(1)
        pot.set_limits(1, 2)

        print("Sistema inicializado. Entrando no loop principal...")
        
        while True:
            try:
                if dado.telas == dado.TELA_INICIAL:
                    lcd.lcd_display_string("**** QUALIFIX **** ", 1, 1)
                    lcd.lcd_display_string("Iniciar", 2, 1)
                    lcd.lcd_display_string("Configuracoes", 3, 1)
                    
                    if pot.get_counter() == 1:
                        lcd.lcd_display_string(">", 2, 0)
                        lcd.lcd_display_string(" ", 3, 0)
                    elif pot.get_counter() == 2:
                        lcd.lcd_display_string(">", 3, 0)
                        lcd.lcd_display_string(" ", 2, 0)
                        
                    if (pot.get_sw_status == 0 and pot.get_counter() == 1) or io.io_rpi.get_aciona_maquina == 1:
                        lcd.lcd_clear()
                        lcd.lcd_display_string("**** AGUARDE ****  ", 1, 1)
                        dado.set_telas(dado.TELA_EXECUCAO)
                        pid.set_control_flag(True)
                        lcd.lcd_clear()
                        time.sleep_ms(300)
                    elif pot.get_sw_status == 0 and pot.get_counter() == 2:
                        pot.set_counter(1)
                        dado.set_telas(dado.TELA_CONFIGURACAO)
                        lcd.lcd_clear()
                        time.sleep_ms(300)

                elif dado.telas == dado.TELA_EXECUCAO:
                    lcd.lcd_display_string("Execucao          ", 1, 1)
                    lcd.lcd_display_string(f"1:{pid.value_temp[0]:.1f} 4:{pid.value_temp[3]:.1f}", 2, 1)
                    lcd.lcd_display_string(f"2:{pid.value_temp[1]:.1f} 5:{pid.value_temp[4]:.1f}", 3, 1)
                    lcd.lcd_display_string(f"3:{pid.value_temp[2]:.1f} 6:{pid.value_temp[5]:.1f}", 4, 1)

                    if pot.get_sw_status == 0 or io.io_rpi.get_aciona_maquina == 1:
                        lcd.lcd_clear()
                        lcd.lcd_display_string("**** AGUARDE ****  ", 1, 1)
                        io.io_rpi.aciona_maquina_pronta(False)  # Desliga a saída que habilita a prensa
                        dado.set_telas(dado.TELA_INICIAL)
                        pid.set_control_flag(False)
                        lcd.lcd_clear()
                        pot.set_counter(1)
                        time.sleep_ms(300)

                elif dado.telas == dado.TELA_CONFIGURACAO:
                    pot.set_limits(1, 3)
                    lcd.lcd_display_string("Configurar:", 1, 1)
                    lcd.lcd_display_string("Temp", 2, 1)
                    lcd.lcd_display_string("PID", 3, 1)
                    lcd.lcd_display_string("Sair", 4, 1)
                    
                    if pot.get_counter() == 1:
                        lcd.lcd_display_string(">", 2, 0)
                        lcd.lcd_display_string(" ", 3, 0)
                        lcd.lcd_display_string(" ", 4, 0)
                        if pot.get_sw_status == 0:
                            dado.set_telas(TELA_CONFIGURACAO_TEMP)
                            lcd.lcd_clear()
                            time.sleep_ms(300)
                    elif pot.get_counter() == 2:
                        lcd.lcd_display_string(" ", 2, 0)
                        lcd.lcd_display_string(">", 3, 0)
                        lcd.lcd_display_string(" ", 4, 0)
                        if pot.get_sw_status == 0:
                            dado.set_telas(TELA_CONFIGURACAO_PID)
                            lcd.lcd_clear()
                            time.sleep_ms(300)
                    elif pot.get_counter() == 3:
                        lcd.lcd_display_string(" ", 2, 0)
                        lcd.lcd_display_string(" ", 3, 0)
                        lcd.lcd_display_string(">", 4, 0)
                        if pot.get_sw_status == 0:
                            dado.set_telas(dado.TELA_INICIAL)
                            lcd.lcd_clear()
                            pot.set_counter(1)
                            time.sleep_ms(300)

                elif dado.telas == TELA_CONFIGURACAO_TEMP:
                    pot.set_limits(1, 6)  # Limita a quantidade de canais para ajuste de setpoint
                    canal = pot.get_counter()
                    lcd.lcd_display_string(f"Canal {canal}", 1, 1)
                    lcd.lcd_display_string(f"Temp: {setpoint_list[canal-1]}C", 2, 1)
                    lcd.lcd_display_string("Pressione para ajustar", 3, 1)

                    if pot.get_sw_status == 0:
                        time.sleep_ms(600)
                        ajt = 1
                        pot.set_limits(10, 300)  # Limita o ajuste de temperatura
                        pot.set_counter(setpoint_list[canal-1])
                        
                        while ajt == 1:
                            setpoint_list[canal-1] = pot.get_counter()
                            lcd.lcd_display_string(f"Temp: {setpoint_list[canal-1]}C", 2, 1)
                            
                            if pot.get_sw_status == 0:
                                save_setpoint_to_file(setpoint_list)  # Salva os setpoints ajustados
                                pid.update_parameters(setpoint_list=setpoint_list)  # Atualiza no PID
                                ajt = 0
                                pot.set_limits(1, 6)
                                pot.set_counter(1)
                                dado.set_telas(dado.TELA_CONFIGURACAO)
                                lcd.lcd_clear()
                                time.sleep_ms(300)
                            time.sleep_ms(100)

                elif dado.telas == TELA_CONFIGURACAO_PID:
                    pot.set_limits(1, 6)  # Limita a quantidade de canais para ajuste de PID
                    canal = pot.get_counter()
                    lcd.lcd_display_string("Ajuste PID", 1, 1)
                    lcd.lcd_display_string(f"Canal {canal}", 2, 1)
                    lcd.lcd_display_string("Kp:{:.2f} Ki:{:.2f}".format(kp_list[canal-1], ki_list[canal-1]), 3, 1)
                    lcd.lcd_display_string("Kd:{:.2f}".format(kd_list[canal-1]), 4, 1)

                    if pot.get_sw_status == 0:
                        time.sleep_ms(600)
                        pot.set_limits(0, 4000)  # Limita o ajuste de PID
                        ajt = 1
                        lcd.lcd_clear()
                        pot.set_counter(int(kp_list[canal-1] * 100))
                        
                        while ajt == 1:
                            lcd.lcd_display_string("Ajuste Kp", 1, 1)
                            kp_list[canal-1] = pot.get_counter() / 100.0
                            lcd.lcd_display_string(f"Kp: {kp_list[canal-1]:.2f}", 2, 1)
                            
                            if pot.get_sw_status == 0:
                                time.sleep_ms(600)
                                ajt = 2
                                lcd.lcd_clear()
                                pot.set_counter(int(ki_list[canal-1] * 100))
                                
                                while ajt == 2:
                                    lcd.lcd_display_string("Ajuste Ki", 1, 1)
                                    ki_list[canal-1] = pot.get_counter() / 100.0
                                    lcd.lcd_display_string(f"Ki: {ki_list[canal-1]:.2f}", 2, 1)
                                    
                                    if pot.get_sw_status == 0:
                                        time.sleep_ms(600)
                                        ajt = 3
                                        lcd.lcd_clear()
                                        pot.set_counter(int(kd_list[canal-1] * 100))
                                        
                                        while ajt == 3:
                                            lcd.lcd_display_string("Ajuste Kd", 1, 1)
                                            kd_list[canal-1] = pot.get_counter() / 100.0
                                            lcd.lcd_display_string(f"Kd: {kd_list[canal-1]:.2f}", 2, 1)
                                            
                                            if pot.get_sw_status == 0:
                                                ajt = 0
                                                pot.set_limits(1, 6)  # Limita a quantidade de canais para ajuste de PID
                                                pot.set_counter(1)
                                                save_pid_values(kp_list, ki_list, kd_list)  # Salva os valores ajustados
                                                pid.update_parameters(kp_list=kp_list, ki_list=ki_list, kd_list=kd_list)
                                                dado.set_telas(dado.TELA_CONFIGURACAO)
                                                lcd.lcd_clear()
                                                time.sleep_ms(300)
                                            time.sleep_ms(100)
                                    time.sleep_ms(100)
                            time.sleep_ms(100)

                # Pequeno delay para evitar sobrecarga do processador
                time.sleep_ms(50)
                
            except Exception as e:
                print(f"Erro no loop principal: {e}")
                time.sleep_ms(1000)  # Pausa em caso de erro

    except KeyboardInterrupt:
        print("\nEncerrando programa...")
    except Exception as e:
        print(f"Erro crítico: {e}")
    finally:
        # Cleanup
        try:
            lcd.lcd_clear()
            pot.cleanup()
            io.io_rpi.cleanup()
            pid.set_control_flag(False)
            pid.stop()
            print("Cleanup concluído. Sistema encerrado.")
        except Exception as e:
            print(f"Erro durante cleanup: {e}")

if __name__ == "__main__":
    main()