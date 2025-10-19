# Controle PID - Raspberry Pi Pico 2

Este projeto foi adaptado do Raspberry Pi Zero W para o **Raspberry Pi Pico 2**, considerando as particularidades da plataforma MicroPython.

## 🔄 Principais Adaptações Realizadas

### 1. **Sistema de GPIO e PWM**
- **RPi.GPIO** → **machine.Pin**
- **PWM Software**: Implementado PWM por software usando threads para permitir frequências baixas (1Hz)
- **Novo mapeamento de pinos** conforme especificado:
  - PWM 1-6: GPIOs 12, 11, 10, 7, 3, 4
  - Máquina Pronta: GPIO 6
  - Entrada Aciona Máquina: GPIO 5

### 2. **Comunicação Serial**
- **pyserial** → **machine.UART**
- UART configurável (padrão: UART0, TX=GP0, RX=GP1)
- Timeout e controle de fluxo adaptados para MicroPython

### 3. **Display LCD I2C**
- **smbus** → **machine.I2C**
- I2C0 do Pi Pico (SDA=GP0, SCL=GP1)
- Detecção automática de endereços I2C

### 4. **Encoder Rotativo (KY040)**
- Pinos: CLK=GP14, DT=GP15, SW=GP16
- **RPi.GPIO.add_event_detect** → **machine.Pin.irq**
- Debounce implementado via software

### 5. **Sistema Threading**
- **threading** → **_thread** (MicroPython)
- Limitação respeitada: máximo 2 threads (Pi Pico 2 tem 2 cores)
- PWM centralizado em uma única thread para economia de recursos

### 6. **Persistência de Dados**
- **json/os** → **ujson** (sem uos, arquivos diretos)
- Arquivos salvos na memória flash do Pi Pico

## 📁 Estrutura dos Arquivos Adaptados

```
Controller/
├── IOs_pico.py         # GPIO, PWM e comunicação UART
├── KY040_pico.py       # Encoder rotativo
├── Lcd_pico.py         # Display LCD I2C
├── PID_pico.py         # Controlador PID com threads
├── Dados_pico.py       # Gerenciamento de estados
main_pico.py            # Programa principal
```

## 🔌 Pinout do Raspberry Pi Pico 2

| Função | GPIO | Descrição |
|--------|------|-----------|
| UART TX | 0 | Transmissão Modbus |
| UART RX | 1 | Recepção Modbus |
| PWM_6 | 3 | Saída PWM Canal 6 |
| PWM_5 | 4 | Saída PWM Canal 5 |
| ENTRADA_MAQUINA | 5 | Entrada digital (botão) |
| MAQUINA_PRONTA | 6 | Saída digital (sinalização) |
| PWM_4 | 7 | Saída PWM Canal 4 |
| PWM_3 | 10 | Saída PWM Canal 3 |
| PWM_2 | 11 | Saída PWM Canal 2 |
| PWM_1 | 12 | Saída PWM Canal 1 |
| KY040_CLK | 14 | Encoder - Clock |
| KY040_DT | 15 | Encoder - Data |
| KY040_SW | 16 | Encoder - Switch |
| I2C0_SDA | 0 | Display LCD (compartilhado) |
| I2C0_SCL | 1 | Display LCD (compartilhado) |

**⚠️ ATENÇÃO**: GPIOs 0 e 1 são compartilhados entre UART e I2C. Configure apenas um protocolo por vez ou use pinos alternativos.

## 🚀 Como Usar

### 1. **Preparação do Pi Pico 2**
```bash
# Instale o MicroPython no Pi Pico 2
# Baixe o firmware em: https://micropython.org/download/rp2-pico/
```

### 2. **Upload dos Arquivos**
- Copie todos os arquivos `*_pico.py` para o Pi Pico 2
- Use Thonny, rshell, ou ampy para transferência

### 3. **Execução**
```python
# No Pi Pico 2, execute:
import main_pico
# ou renomeie main_pico.py para main.py para execução automática
```

## ⚙️ Configurações Importantes

### **PWM Software**
```python
# Período padrão: 1.0 segundo (1Hz)
# Para alterar a frequência:
io.io_rpi.set_pwm_period(0.5)  # 2Hz
io.io_rpi.set_pwm_period(2.0)  # 0.5Hz
```

### **UART Modbus**
```python
# Configuração padrão
uart_id = 0        # UART0
baudrate = 9600    # Baud rate
tx_pin = 0         # GP0
rx_pin = 1         # GP1
timeout = 1.0      # 1 segundo
```

### **I2C Display**
```python
# Configuração padrão I2C0
sda_pin = 0        # GP0 (compartilhado com UART TX)
scl_pin = 1        # GP1 (compartilhado com UART RX)
freq = 100000      # 100kHz
```

## 🔧 Limitações e Considerações

### **Threading**
- **Máximo 2 threads simultâneas** (Pi Pico 2 tem 2 cores)
- PWM centralizado em uma thread para todos os canais
- PID executa em thread separada

### **Memória**
- **264KB RAM** vs 512MB do Pi Zero W
- Arquivos JSON mantidos pequenos
- Uso otimizado de variáveis

### **Performance**
- **133MHz** vs 1GHz do Pi Zero W
- Intervalos de controle ajustados (mínimo 0.5s)
- PWM software pode ter jitter em alta carga

### **Persistência**
- Arquivos salvos na **memória flash interna** (2MB)
- Sem sistema de arquivos completo como Linux
- Backup manual necessário

## 🐛 Troubleshooting

### **Erro de UART/I2C**
```python
# Se houver conflito entre UART e I2C nos pinos 0/1:
# Opção 1: Use UART1
IO_MODBUS(uart_id=1, tx_pin=4, rx_pin=5)

# Opção 2: Use I2C1
Lcd(sda_pin=2, scl_pin=3, i2c_id=1)
```

### **PWM não funciona**
```python
# Verifique se a thread PWM está rodando:
print(io.io_rpi.pwm_thread_running)

# Reinicie se necessário:
io.io_rpi.cleanup()
io = IO_MODBUS()
```

### **Encoder não responde**
```python
# Verifique as interrupções:
pot.cleanup()
pot = KY040()
```

## 📈 Melhorias Futuras Possíveis

1. **PWM Hardware**: Usar machine.PWM para frequências > 10Hz
2. **Dual Core**: Distribuir melhor as tarefas entre os 2 cores
3. **Web Interface**: Interface via WiFi (com Pico W)
4. **Logging**: Sistema de logs para debug
5. **Backup automático**: Sincronização automática de configurações

## 🤝 Compatibilidade

| Recurso | Pi Zero W | Pi Pico 2 | Status |
|---------|-----------|-----------|--------|
| GPIO | ✅ | ✅ | ✅ Adaptado |
| PWM | ✅ | ⚠️ | ✅ Software |
| UART | ✅ | ✅ | ✅ Adaptado |
| I2C | ✅ | ✅ | ✅ Adaptado |
| Threading | ✅ | ⚠️ | ✅ Limitado |
| File System | ✅ | ⚠️ | ✅ Básico |
| Performance | ✅ | ⚠️ | ✅ Reduzida |

---

**Desenvolvido para Raspberry Pi Pico 2 + MicroPython**  
*Adaptação do projeto original para Pi Zero W*