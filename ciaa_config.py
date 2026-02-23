"""
CIAA-ACC Configuration Module
Constantes de memoria, enumeraciones y funciones para generar comandos AXI.
"""

from enum import Enum

# ============================================================================
# Direcciones Base de Memoria AXI-Lite
# ============================================================================

DATA_BASE_ADDR = 0x43C00000      # Control principal (10-bit address space)
PREPROC_BASE_ADDR = 0x43C30000   # Preprocessing (6-bit address space)
FIFO_READ_BASE_ADDR = 0x43C00200 # Lectura de FIFO de datos

# ============================================================================
# Offsets de Registros (DATA_BASE_ADDR)
# ============================================================================

RESET_ASYNC_OFFSET = 0x004        # Reset asíncrono de periféricos
FIFORST_OFFSET = 0x008            # Reset de FIFO
OSC_MIX_BEAM_0_OFFSET = 0x00C     # Frecuencia mixer beam 0
ENABLE_OFFSET = 0x010             # Enable global del sistema
EXT_TRIGGER_EN_OFFSET = 0x024     # Trigger externo
OSC_DEBUG_FREQ_OFFSET = 0x034     # Frecuencia oscilador debug
DEBUG_CONTROL_OFFSET = 0x080      # Control de modo debug
FIFOFLAGSRST_OFFSET = 0x180       # Flags/status de FIFO

# ============================================================================
# Offsets de Registros (PREPROC_BASE_ADDR)
# ============================================================================

FIFO_INPUT_MUX_OFFSET = 0x04      # Selector de entrada al FIFO
DATA_SOURCE_MUX_OFFSET = 0x08     # Selector de fuente de datos
LOCAL_OSC_FREQ_OFFSET = 0x34      # Frecuencia oscilador local (PINC 32b)
BEAM_FREQ_OFFSET = 0x0C           # Base para frec. de beams (ch_freq_1)
BEAM_FREQ_STRIDE = 0x08           # Paso entre registros de frec. de beam

# ============================================================================
# Ubicación de Ejecutables en CIAA
# ============================================================================

ELFS_LOCATION = '/mnt/currentVersions/'

# ============================================================================
# Enumeraciones de Configuración
# ============================================================================

class DebugMode(Enum):
    """Modos de debug (DEBUG_Control_base register)"""
    DISABLED = 0x0                  # Normal: datos de ADC
    MIDSCALE_SH = 0x1              # Midscale sample/hold
    PLUS_FULLSCALE_SH = 0x2        # Positive full-scale
    MINUS_FULLSCALE_SH = 0x3       # Negative full-scale
    USR_W1 = 0x8                   # User-defined word 1
    USR_W2 = 0x9                   # User-defined word 2
    ONEX_BITSYNC = 0xA             # Bit sync test pattern
    ONEBIT_HIGH = 0xB              # Single bit high
    MIXED_FREQ = 0xC               # Mixed frequency test
    DESERIALIZER = 0xD             # Deserializer output
    CONT_NBITS = 0xF               # N-bit counter (útil para test)
    
    def to_string(self):
        names = {
            0x0: 'DISABLED (ADC Data)',
            0x1: 'Midscale S/H',
            0x2: '+FullScale S/H',
            0x3: '-FullScale S/H',
            0x8: 'User Word 1',
            0x9: 'User Word 2',
            0xA: '1x Bit Sync',
            0xB: 'One Bit High',
            0xC: 'Mixed Freq',
            0xD: 'Deserializer Out',
            0xF: 'Counter (N-bits)'
        }
        return names.get(self.value, f'Unknown (0x{self.value:X})')


class DataSource(Enum):
    """Fuentes de datos (DATA_Source_Mux_Control)"""
    DATOS_ADC = 0      # Datos de ADC
    OSC_LOC = 1        # Oscilador local (tono único)
    CONTADOR = 2       # Contador de prueba
    
    def to_string(self):
        names = {
            0: 'ADC Data',
            1: 'Local Oscillator (Single Tone)',
            2: 'Counter Pattern'
        }
        return names[self.value]


class FIFOInput(Enum):
    """Opciones de entrada al FIFO (FIFO_Input_Mux_Control)"""
    NONE = 0                    # Sin datos
    PREPROC_DATA = 1           # Datos con preprocessing completo
    COUNTER_POST_PROC = 2      # Contador post-procesamiento
    RAW_DATA = 3               # Datos raw de ADC (sin procesar)
    MUX_DATA = 4               # Salida directa del mux de datos
    BAND_MIXER = 5             # Salida del mixer de banda
    BAND_FILTER = 6            # Salida del filtro de banda
    CH_MIXER = 7               # Salida del mixer de canal
    
    def to_string(self):
        names = {
            0: 'None',
            1: 'Preprocessed Data (Band FIR + Ch Mixer + Ch FIR)',
            2: 'Counter (Post-Processing)',
            3: 'Raw ADC Data (Bypass)',
            4: 'Data Mux Output',
            5: 'Band Mixer Output (NCO fijo)',
            6: 'Band Filter Output',
            7: 'Channel Mixer Output (NCO configurable)'
        }
        return names[self.value]


# ============================================================================
# Funciones para Generar Comandos AXI
# ============================================================================

def axi_write_cmd(reg_addr, data):
    """
    Genera comando para escribir registro AXI via axi_rw_test.elf
    
    :param reg_addr: Dirección del registro (int)
    :param data: Valor a escribir (int)
    :return: Comando completo como string
    """
    cmd = f'{ELFS_LOCATION}axi_rw_test.elf w {reg_addr:x} {data:x}\n'
    return cmd


def axi_read_cmd(reg_addr):
    """
    Genera comando para leer registro AXI
    
    :param reg_addr: Dirección del registro (int)
    :return: Comando completo como string
    """
    cmd = f'{ELFS_LOCATION}axi_rw_test.elf r {reg_addr:x}\n'
    return cmd


# ============================================================================
# Mapa rápido de registros (mantener en sync con ADC_DataSheet.md §3.5)
# ============================================================================

REGISTER_MAP_SNIPPET = [
    (
        'DATA 0x43C00000',
        [
            ('RESET_ASYNC', DATA_BASE_ADDR + RESET_ASYNC_OFFSET),
            ('FIFORST', DATA_BASE_ADDR + FIFORST_OFFSET),
            ('ENABLE', DATA_BASE_ADDR + ENABLE_OFFSET),
            ('DEBUG_CONTROL', DATA_BASE_ADDR + DEBUG_CONTROL_OFFSET),
            ('FIFOFLAGSRST', DATA_BASE_ADDR + FIFOFLAGSRST_OFFSET),
        ],
    ),
    (
        'PREPROC 0x43C30000',
        [
            ('BEAM_FREQ_CH0', PREPROC_BASE_ADDR + BEAM_FREQ_OFFSET + 0 * BEAM_FREQ_STRIDE),
            ('BEAM_FREQ_CH1', PREPROC_BASE_ADDR + BEAM_FREQ_OFFSET + 1 * BEAM_FREQ_STRIDE),
            ('BEAM_FREQ_CH2', PREPROC_BASE_ADDR + BEAM_FREQ_OFFSET + 2 * BEAM_FREQ_STRIDE),
            ('BEAM_FREQ_CH3', PREPROC_BASE_ADDR + BEAM_FREQ_OFFSET + 3 * BEAM_FREQ_STRIDE),
            ('BEAM_FREQ_CH4', PREPROC_BASE_ADDR + BEAM_FREQ_OFFSET + 4 * BEAM_FREQ_STRIDE),
            ('LOCAL_OSC_FREQ', PREPROC_BASE_ADDR + LOCAL_OSC_FREQ_OFFSET),
            ('FIFO_INPUT_MUX', PREPROC_BASE_ADDR + FIFO_INPUT_MUX_OFFSET),
            ('DATA_SOURCE_MUX', PREPROC_BASE_ADDR + DATA_SOURCE_MUX_OFFSET),
        ],
    ),
]


def format_register_map_snippet():
    """
    Devuelve un string listo para imprimir con las direcciones clave.
    Útil para validar que código y documentación coinciden.
    """
    lines = []
    for region, entries in REGISTER_MAP_SNIPPET:
        lines.append(f'[{region}]')
        for name, addr in entries:
            lines.append(f'  {name}: 0x{addr:08X}')
    return '\n'.join(lines)


# ============================================================================
# Comandos de Control del Sistema
# ============================================================================

def reset_async_cmd():
    """Reset asíncrono de periféricos"""
    return axi_write_cmd(DATA_BASE_ADDR + RESET_ASYNC_OFFSET, 10)


def reset_fifo_cmd():
    """Reset del FIFO de datos"""
    return axi_write_cmd(DATA_BASE_ADDR + FIFORST_OFFSET, 1)


def enable_cmd(enable=True):
    """
    Enable/disable del sistema
    
    :param enable: True para habilitar, False para deshabilitar
    :return: Comando AXI
    """
    val = 1 if enable else 0
    return axi_write_cmd(DATA_BASE_ADDR + ENABLE_OFFSET, val)


def set_debug_mode_cmd(mode_value):
    """
    Configura modo de debug
    
    :param mode_value: Valor del modo (int, ej: 0xF para counter)
    :return: Comando AXI
    """
    return axi_write_cmd(DATA_BASE_ADDR + DEBUG_CONTROL_OFFSET, mode_value)


def set_fifo_input_cmd(fifo_input_value):
    """
    Configura entrada del FIFO
    
    :param fifo_input_value: Valor del mux (0-7)
    :return: Comando AXI
    """
    return axi_write_cmd(PREPROC_BASE_ADDR + FIFO_INPUT_MUX_OFFSET, fifo_input_value)


def set_data_source_cmd(source_value):
    """
    Configura fuente de datos
    
    :param source_value: Valor de la fuente (0-2)
    :return: Comando AXI
    """
    return axi_write_cmd(PREPROC_BASE_ADDR + DATA_SOURCE_MUX_OFFSET, source_value)


def set_local_osc_freq_cmd(freq_mhz):
    """
    Configura frecuencia del oscilador local
    
    :param freq_mhz: Frecuencia en MHz (float)
    :return: Comando AXI
    
    Fórmula: PINC = abs(freq_MHz * 4 * 2^32 / 260.0)
    """
    freq_conf = int(abs(freq_mhz) * 4 * 2**32 / 260.0)
    return axi_write_cmd(PREPROC_BASE_ADDR + LOCAL_OSC_FREQ_OFFSET, freq_conf)


def set_beam_freq_cmd(beam_number, freq_mhz):
    """
    Configura frecuencia de un beam específico
    
    :param beam_number: Número de beam (0-4)
    :param freq_mhz: Frecuencia en MHz (float, típicamente 435-438 MHz)
    :return: Comando AXI
    
    Proceso:
    1. Undersampling: freq_undersampled = freq - 7*65 MHz
    2. Banda base: freq_BB = |freq_undersampled| + 18.5 MHz
    3. DDS phase increment: PINC = freq_BB * 2^32 / 260.0
    """
    freq_undersampled = freq_mhz - 7 * 65
    freq_BB = abs(freq_undersampled) + 18.5
    freq_conf = int(freq_BB * 2**32 / 260.0)

    reg_addr = PREPROC_BASE_ADDR + BEAM_FREQ_OFFSET + beam_number * BEAM_FREQ_STRIDE
    print(f'beam_number', beam_number, 'freq_mhz', freq_mhz)
    print(f'freq_undersampled', freq_undersampled)
    print(f'freq_BB', freq_BB)
    print(f'freq_conf', f"0x{freq_conf:08X}")
    
    return axi_write_cmd(reg_addr, freq_conf)


def set_channel_mixer_freq_cmd(channel_number, freq_mhz):
    """
    Configura frecuencia del NCO de la etapa final de mezcla (CH_MIXER).
    Esta es la FRECUENCIA DEL OSCILADOR (parámetro de control).

    :param channel_number: Número de canal NCO (0-4)
    :param freq_mhz: Frecuencia de oscilación del NCO en MHz (típicamente 0-32.5)
    :return: Comando AXI

    Fórmula directa DDS (clock=260 MHz):
    PINC = int(abs(freq_MHz) * 2^32 / 260.0)
    
    Ejemplo: Para mezclar -3 MHz de entrada del band mixer a ~0 Hz,
    configura CH_MIXER_NCO = 3 MHz
    """
    freq_conf = int(abs(freq_mhz) * 2**32 / 260.0)
    reg_addr = PREPROC_BASE_ADDR + BEAM_FREQ_OFFSET + channel_number * BEAM_FREQ_STRIDE
    return axi_write_cmd(reg_addr, freq_conf)


# ============================================================================
# Comandos de Ejecución de Aplicaciones
# ============================================================================

def startup_cmd():
    """
    Ejecuta startup.elf (calibración IDELAY de ADCs)
    ⚠️ RESETEA TODOS LOS REGISTROS AXI A 0x00000000
    """
    return f'{ELFS_LOCATION}startup.elf\n'


def launch_acq_cmd():
    """
    Lanza sist_adq.elf para streaming UDP
    Requiere archivo client_config con configuración de red
    """
    return f'{ELFS_LOCATION}sist_adq_crc.elf {ELFS_LOCATION}client_config\n'


def set_beam_selector_cmd(beam_number):
    """
    Selecciona cuál de los 5 NCOs de canal es visible en la salida.
    
    :param beam_number: Número de beam/canal NCO (0-4)
    :return: Comando AXI
    
    Solo el beam seleccionado tiene su salida agregada al FIFO.
    Los otros 4 NCOs siguen procesando pero no son visibles.
    """
    reg_addr = PREPROC_BASE_ADDR + 0x38  # BEAM_SELECTOR offset
    return axi_write_cmd(reg_addr, beam_number & 0x7)


def reboot_cmd():
    """Reinicia Linux en la placa CIAA."""
    return 'reboot\n'


# ============================================================================
# Utilidades de Sample Rate
# ============================================================================

def calculate_sample_rate(clk_divider=0):
    """
    Calcula sample rate efectivo basado en CLK_DIVIDER
    
    :param clk_divider: Valor del divisor de clock (0 = sin división)
    :return: Sample rate en Hz
    
    ADC base rate: 65 MSPS
    Sample rate = 65e6 / (clk_divider + 1)
    """
    return 65e6 / (clk_divider + 1)


def get_packet_sample_rate(clk_divider=0):
    """
    Calcula la tasa de llegada de paquetes UDP
    
    Cada paquete tiene 21 samples por canal.
    Tasa de paquetes = sample_rate / 21
    
    :param clk_divider: Valor del divisor de clock
    :return: Paquetes por segundo
    """
    fs = calculate_sample_rate(clk_divider)
    return fs / 21
