# CIAA-ACC Control UI

Interfaz gráfica PyQt5 para control remoto del sistema de adquisición de datos CIAA-ACC via SSH. **No incluye visualización de datos** (usar `gnuradio_streaming/` para eso).

## 🎯 Funcionalidad

- **Conexión SSH** a CIAA-ACC (192.168.0.22)
- **Configuración de registros AXI-Lite:**
  - Debug Mode (patrones de prueba)
  - Data Source (ADC/Oscillator/Counter)
  - FIFO Input Mux (etapa del pipeline)
  - Local Oscillator frequency (0-32.5 MHz)
  - Beam frequencies (5 beams, 435-438 MHz)
- **Control de adquisición:**
  - Reset system / FIFO
  - Enable / Disable acquisition
  - Launch UDP streaming
- **Consola SSH** en tiempo real
- **Presets rápidos** para configuraciones comunes

---

## 📦 Requisitos

### Python 3.12+ con paquetes:
```bash
pip install PyQt5 paramiko
```

### Hardware:
- CIAA-ACC en red (192.168.0.22)
- SSH habilitado (usuario `root`, sin contraseña)

---

## 🚀 Uso

### Ejecución:
```bash
cd F:\Proyectos\sist_adq_dbf\UI_control
python main.py
```

### Flujo de Trabajo Típico:

1. **Iniciar Aplicación**
   - Conecta automáticamente via SSH
   - Opcionalmente ejecuta `startup.elf` (calibración IDELAY)

2. **Configurar Sistema**
   - **Opción A:** Usar presets (tab "Presets")
   - **Opción B:** Configurar manualmente cada parámetro

3. **Iniciar Adquisición**
   - Botón "ENABLE Acquisition"
   - Botón "LAUNCH UDP Streaming"
   - Verificar en consola que no hay errores

4. **Visualizar Datos**
   - Abrir GNU Radio Companion (desde Radioconda)
   - Ejecutar flowgraph en `gnuradio_streaming/ciaa_udp_receiver.grc`
   - Datos deben aparecer en sinks

---

## ⚙️ Configuraciones Presets

### 🔢 Counter Test
```
Debug Mode: CONT_NBITS (0xF)
Data Source: CONTADOR
FIFO Input: MUX_DATA
```
**Uso:** Validar desempaquetado UDP y continuidad de datos.

### 📡 ADC Raw Data
```
Debug Mode: DISABLED (0x0)
Data Source: DATOS_ADC
FIFO Input: RAW_DATA
```
**Uso:** Captura directa de ADC sin procesamiento.

### ⚙️ Preprocessed Data
```
Debug Mode: DISABLED (0x0)
Data Source: DATOS_ADC
FIFO Input: PREPROC_DATA
```
**Uso:** Datos con beamforming y filtrado completo.

---

## 📖 Arquitectura de Registros

### Direcciones Base:
- `DATA_BASE_ADDR = 0x43C00000` (Control principal)
- `PREPROC_BASE_ADDR = 0x43C30000` (Preprocessing)

### Registros Clave:
| Offset | Registro | Función |
|--------|----------|---------|
| +0x004 | RESET_ASYNC | Reset asíncrono |
| +0x008 | FIFORST | Reset de FIFO |
| +0x010 | ENABLE | Enable global |
| +0x080 | DEBUG_Control | Modo de debug |
| +0x180 | FIFOFLAGSRST | Flags de FIFO |

Ver `ciaa_config.py` para detalles completos.

---

## 🐛 Troubleshooting

### No conecta SSH:
```
✗ No se pudo conectar a CIAA (192.168.0.22)
```
**Solución:**
- Verificar ping: `ping 192.168.0.22`
- Revisar cable Ethernet
- Confirmar IP de CIAA con `ip addr` en consola serial

### Después de `startup.elf` no funciona:
**Problema:** `startup.elf` resetea TODOS los registros AXI a 0x00000000.

**Solución:** Reconfigurar usando preset o manualmente:
1. Tab "Presets" → Elegir configuración
2. O: Manual reset → configurar cada parámetro → Enable

### Comandos manuales SSH:
Usar campo de texto inferior en consola:
```bash
# Leer registro
./axi_rw_test.elf r 43c00080

# Escribir registro
./axi_rw_test.elf w 43c00080 f
```

---

## 📁 Estructura de Archivos

```
UI_control/
├── main.py              # Aplicación PyQt5 principal
├── sshClient.py         # Cliente SSH con Paramiko
├── ciaa_config.py       # Constantes, enums, comandos AXI
└── README.md            # Esta documentación
```

---

## 🔗 Integración con GNU Radio

Esta UI **solo controla** el hardware. Para **visualizar** datos:

1. Configurar adquisición aquí (UI_control)
2. Lanzar streaming con botón "LAUNCH UDP Streaming"
3. Abrir GNU Radio flowgraph:
   ```bash
   conda activate gnuradio  # O tu entorno Radioconda
   cd ../gnuradio_streaming
   gnuradio-companion ciaa_udp_receiver.grc
   ```
4. Ejecutar flowgraph (F6) y verificar FFT/Time plots

---

## ⚠️ Notas Importantes

- **startup.elf resetea registros:** Después de ejecutarlo, reconfigura todo.
- **Puerto UDP:** Por defecto 9999 (configurar en client_config de CIAA).
- **Sample Rate:** Depende de CLK_DIVIDER (ver `ciaa_config.calculate_sample_rate()`).
- **FIFO Overflow:** Normal si tasa de salida < tasa de entrada (ver flags en consola).

---

## 📚 Referencias

- Mapa de memoria completo: `.github/copilot-instructions.md`
- Estructura de paquetes UDP: `UDP_STREAMING_TEST_RESULTS.md`
- Tests de validación: Scripts `test_*.py` en raíz del proyecto

---

## 🆘 Soporte

Para problemas o mejoras, revisar:
- Logs en consola SSH (dentro de la UI)
- Documentación del proyecto en `.github/copilot-instructions.md`
- Scripts de diagnóstico en raíz (ej: `diagnose_streaming.py`)
