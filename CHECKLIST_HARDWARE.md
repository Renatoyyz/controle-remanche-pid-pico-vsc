# ✅ CHECKLIST PRÉ-TESTE COM HARDWARE FÍSICO

## 🎯 CONFIGURAÇÃO DE PINOS CORRIGIDA

### ✅ Pinos Confirmados:

**LCD I2C 20x4:**
- **SDA** → GPIO 8 (I2C0)
- **SCL** → GPIO 9 (I2C0)

**UART Modbus:**
- **TX** → GPIO 0 (UART0)
- **RX** → GPIO 1 (UART0)

**Encoder KY040:**
- **CLK** → GPIO 14
- **DT** → GPIO 15
- **SW** → GPIO 16

✅ **NÃO HÁ CONFLITO DE PINOS!** Todos os pinos são únicos.

---

## ✅ CORREÇÕES REALIZADAS

### 1. ✅ Pinos I2C Atualizados
- `Controller/Lcd_pico.py` → SDA=GP8, SCL=GP9
- `Controller/Lcd_pico_safe.py` → SDA=GP8, SCL=GP9

### 2. ✅ F-strings Corrigidas em main_pico.py
Todas as f-strings foram substituídas por `.format()` para compatibilidade com MicroPython:
- Linhas 151-159: Exibição de temperaturas
- Linhas 210-212: Configuração de temperatura
- Linhas 239: Configuração PID
- Linhas 253, 264, 274: Ajuste Kp, Ki, Kd

### 3. ✅ Scripts de Teste Criados
- `test_i2c_scanner.py` - Scanner I2C para detectar endereço do LCD
- `test_lcd.py` - Teste individual do LCD
- `test_encoder.py` - Teste individual do encoder
- `test_modbus.py` - Teste individual UART/Modbus

---

## 📋 CHECKLIST HARDWARE

### 1. 🔌 Conexões Elétricas

#### LCD I2C 20x4
- [ ] **VCC** → 5V ou 3.3V (verificar compatibilidade do LCD)
- [ ] **GND** → GND
- [ ] **SDA** → GPIO 0 (Pin 1)
- [ ] **SCL** → GPIO 1 (Pin 2)
- [ ] **Endereço I2C**: 0x27 ou 0x3F (verificar com scanner I2C)
- [ ] **Pull-ups**: Verificar se o módulo tem resistores de 4.7kΩ embutidos

#### Encoder Rotativo KY040
- [ ] **CLK** → GPIO 14 (Pin 19)
- [ ] **DT** → GPIO 15 (Pin 20)
- [ ] **SW** → GPIO 16 (Pin 21)
- [ ] **VCC** → 3.3V
- [ ] **GND** → GND

#### Conversor Serial (USB-TTL ou RS485)
- [ ] **TX (Pico)** → GPIO 0 (Pin 1) - **⚠️ CONFLITO COM SDA!**
- [ ] **RX (Pico)** → GPIO 1 (Pin 2) - **⚠️ CONFLITO COM SCL!**
- [ ] **GND** → GND comum

⚠️ **PROBLEMA CRÍTICO DETECTADO**: Configuração usa mesmos pinos para I2C e UART!

---

### 2. 🚨 CONFLITO DE PINOS IDENTIFICADO!

O código atual tem um **conflito grave**:

```python
# Em Lcd_pico.py
SDA_PIN = 0  # GPIO 0
SCL_PIN = 1  # GPIO 1

# Em IOs_pico.py
TX_PIN = 0   # GPIO 0 (UART TX)
RX_PIN = 1   # GPIO 1 (UART RX)
```

**GP0 e GP1 não podem ser usados simultaneamente para I2C E UART!**

#### 📌 Solução Recomendada - Remap de Pinos:

**Opção A - Usar I2C1 para LCD:**
```python
# Lcd_pico.py
I2C_ID = 1   # Mudar para I2C1
SDA_PIN = 26  # GPIO 26 (I2C1 SDA)
SCL_PIN = 27  # GPIO 27 (I2C1 SCL)

# IOs_pico.py (manter)
UART_ID = 0
TX_PIN = 0   # GPIO 0 (UART0 TX)
RX_PIN = 1   # GPIO 1 (UART0 RX)
```

**Opção B - Usar UART1 para Modbus:**
```python
# Lcd_pico.py (manter)
I2C_ID = 0
SDA_PIN = 0   # GPIO 0 (I2C0 SDA)
SCL_PIN = 1   # GPIO 1 (I2C0 SCL)

# IOs_pico.py
UART_ID = 1
TX_PIN = 4   # GPIO 4 (UART1 TX)
RX_PIN = 5   # GPIO 5 (UART1 RX)
```

**Recomendação:** Use **Opção A** (I2C1 para LCD) para manter compatibilidade com hardware Modbus existente.

---

### 3. ⚙️ Configurações de Software

#### Verificar Constantes no Código:
- [ ] **Endereços Modbus** dos sensores (adr = [1, 2, 3, 4, 5, 6])
- [ ] **Baudrate UART**: 9600 (padrão Modbus)
- [ ] **Pinos PWM**: GP17-GP22 (verificar se estão livres)
- [ ] **Setpoints iniciais**: 50°C (ajustar conforme necessidade)
- [ ] **Constantes PID**: Kp=1.0, Ki=0.1, Kd=0.05 (ajustar conforme resposta do sistema)

#### Arquivos de Configuração:
- [ ] `setpoint_list.json` criado automaticamente
- [ ] `pid_values.json` criado automaticamente
- [ ] Verificar espaço em flash do Pico (~1.4MB disponível)

---

### 4. 🧪 Testes Graduais Recomendados

#### Fase 1: Teste Individual de Componentes
```python
# 1. Testar apenas LCD
from Controller.Lcd_pico import Lcd
lcd = Lcd()
lcd.lcd_display_string("Teste LCD", 1, 1)
lcd.lcd_display_string("Linha 2", 2, 1)

# 2. Testar apenas Encoder
from Controller.KY040_pico import KY040
encoder = KY040(14, 15, 16, 1, 10)
print(encoder.getValue())

# 3. Testar apenas UART/Modbus
from Controller.IOs_pico import IO_MODBUS
modbus = IO_MODBUS([1], 0, 0, 1, 9600)
temp = modbus.get_temperature_channel(1)
print(f"Temperatura: {temp}")
```

#### Fase 2: Teste de Integração
- [ ] Inicializar todos os componentes sem PID ativo
- [ ] Verificar leituras de temperatura
- [ ] Testar navegação no menu com encoder
- [ ] Verificar display LCD

#### Fase 3: Teste Completo
- [ ] Ativar controle PID
- [ ] Monitorar temperaturas
- [ ] Verificar acionamento PWM
- [ ] Testar salvamento de configurações

---

### 5. 🛠️ Ferramentas de Debug

#### Scanner I2C (verificar endereço do LCD):
```python
from machine import I2C, Pin
i2c = I2C(1, scl=Pin(27), sda=Pin(26), freq=400000)
devices = i2c.scan()
print("Dispositivos I2C:", [hex(d) for d in devices])
```

#### Monitor Serial UART:
```python
from machine import UART, Pin
uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))
print("UART configurado. Aguardando dados...")
while True:
    if uart.any():
        data = uart.read()
        print("Recebido:", data.hex())
```

---

### 6. ⚡ Verificações Elétricas

- [ ] **Alimentação**: 5V estável via USB ou fonte externa
- [ ] **Corrente**: Verificar se fonte suporta LCD + Pico + periféricos (~500mA)
- [ ] **Aterramento**: GND comum entre todos os dispositivos
- [ ] **Cabos**: Máximo 30cm para I2C, usar cabos blindados para Modbus
- [ ] **Isolamento**: Conversor USB-RS485 isolado (se possível)

---

### 7. 📦 Biblioteca i2c_lcd Necessária?

O código atual implementa o driver I2C LCD manualmente. Verificar se precisa de bibliotecas externas:

- [ ] Verificar se `machine.I2C` está disponível no MicroPython
- [ ] Testar comunicação I2C básica primeiro
- [ ] O driver customizado `i2c_device` deve funcionar sem bibliotecas extras

---

## 🚀 AÇÃO IMEDIATA NECESSÁRIA

### Antes de conectar o hardware:

1. **RESOLVER CONFLITO DE PINOS** (escolher Opção A ou B acima)
2. **CORRIGIR main_pico.py** (substituir f-strings por .format())
3. **CRIAR SCRIPT DE TESTE INDIVIDUAL** para cada componente

### Arquivos para modificar:

1. `Controller/Lcd_pico.py` - Alterar para I2C1 (GP26/GP27)
2. `main_pico.py` - Corrigir f-strings nas linhas de display

---

## ✅ RESUMO

### O que está OK:
- ✅ Lógica do código testada e funcionando (modo simulação)
- ✅ Persistência de dados em JSON
- ✅ Controle PID implementado
- ✅ Threading com fallback
- ✅ Tratamento de erros robusto

### O que precisa corrigir ANTES dos testes:
- ❌ **Conflito GPIO 0/1** (I2C vs UART)
- ❌ **f-strings em main_pico.py**
- ⚠️ **Verificar endereço I2C do LCD** (0x27 ou 0x3F)
- ⚠️ **Testar componentes individualmente**

---

**Deseja que eu corrija o conflito de pinos e as f-strings agora?** 🛠️