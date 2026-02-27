#!/usr/bin/env python3
"""
CIAA-ACC Control UI
Interfaz gráfica PyQt5 para control remoto del sistema de adquisición
vía SSH. NO incluye visualización de datos (usar gnuradio_streaming).
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QPalette
import sys
import os
import datetime

# Agregar directorio actual al path para imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sshClient
import ciaa_config as config

def textClickHandler(window, qline: QLineEdit):
    """Maneja comandos manuales escritos en el campo de texto"""
    if window.ssh and window.ssh.isConnected:
        cmd = qline.text().strip()
        if cmd:
            window.write_ssh(cmd)
            qline.clear()


class BeamFreqSetter:
    """Widget para configurar frecuencia de NCO en la mezcla final (CH_MIXER)."""
    
    def __init__(self, window, beamNumber):
        self.window = window
        self.beamNumber = beamNumber
        self.layout = QHBoxLayout()
        
        # LineEdit para entrada directa
        self.lineEdit = QLineEdit(alignment=Qt.AlignCenter)
        self.lineEdit.setPlaceholderText("Freq (MHz)")
        self.lineEdit.returnPressed.connect(self.apply_frequency)
        self.layout.addWidget(self.lineEdit, 1)
        
        # Slider para ajuste visual (0-32.5 MHz)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(32500)
        self.slider.setValue(3000)  # Default: 3 MHz
        self.slider.valueChanged.connect(
            lambda: self.lineEdit.setText(f"{self.slider.value()/1000:.3f}")
        )
        self.slider.sliderReleased.connect(self.apply_frequency)
        self.layout.addWidget(self.slider, 2)
    
    def apply_frequency(self):
        """Calcula y escribe el comando de configuración de frecuencia"""
        try:
            freq = float(self.lineEdit.text())
            cmd = config.set_channel_mixer_freq_cmd(self.beamNumber, freq)
            self.window.write_ssh(cmd)
        except ValueError:
            self.window.log_message(f"ERROR: Frecuencia inválida para Beam {self.beamNumber}")
    
    def get_layout(self):
        return self.layout


class MainWindow(QMainWindow):
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CIAA-ACC Control UI")
        self.resize(800, 900)
        
        # Conexión SSH
        self.ssh = None
        self.datetime_configured = None  # Almacena fecha/hora configurada
        
        # Estados de botones toggle
        self.acquisition_enabled = False
        self.streaming_active = False
        
        self.connect_ssh()
        
        # Setup UI
        self.init_ui()
        
        # Auto-ejecutar startup (calibración IDELAY)
        if self.ssh and self.ssh.isConnected:
            reply = QMessageBox.question(
                self, 
                'Calibración Inicial',
                '¿Ejecutar startup.elf para calibrar IDELAY?\n(Resetea registros, requiere reconfiguración)',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.execute_startup()
    
    def connect_ssh(self):
        """Establece conexión SSH con CIAA"""
        try:
            self.ssh = sshClient.ShellHandler()
            if self.ssh.isConnected:
                print(f"✓ Conectado a CIAA (192.168.0.22)")
                
                # Configurar fecha y hora automáticamente
                self.set_ciaa_datetime()
            else:
                print("✗ No se pudo conectar a CIAA")
                QMessageBox.warning(
                    self, 
                    'Conexión SSH',
                    'No se pudo conectar a CIAA (192.168.0.22).\n'
                    'Verifique red y que CIAA esté encendida.'
                )
        except Exception as e:
            print(f"Error SSH: {e}")
            self.ssh = None
            QMessageBox.critical(self, 'Error', f'Error conectando a CIAA:\n{e}')
    
    def set_ciaa_datetime(self):
        """Configura la fecha y hora actual en la CIAA vía SSH"""
        if not self.ssh or not self.ssh.isConnected:
            print("✗ No hay conexión SSH para configurar fecha/hora")
            return
        
        try:
            now = datetime.datetime.now()
            # Formato: 'YYYY-MM-DD HH:MM:SS'
            date_str = now.strftime('%Y-%m-%d %H:%M:%S')
            
            print(f"[INFO] Configurando fecha/hora en CIAA: {date_str}")
            
            cmd = f'date -s "{date_str}"'
            result = self.ssh.execute(cmd)
            
            # Parsear resultado
            if isinstance(result, tuple) and len(result) > 1:
                stdout_lines = result[1]
                if stdout_lines:
                    configured_time = stdout_lines[0].strip() if isinstance(stdout_lines[0], str) else date_str
                    print(f"[OK] Fecha/hora configurada: {configured_time}")
                    self.datetime_configured = now
                    
                    # Actualizar UI si ya existe el label
                    if hasattr(self, 'status_label'):
                        self.update_connection_status()
                else:
                    print(f"[OK] Comando ejecutado: {date_str}")
                    self.datetime_configured = now
            else:
                print(f"[OK] Fecha/hora configurada: {date_str}")
                self.datetime_configured = now
                
        except Exception as e:
            print(f"[ERROR] No se pudo configurar fecha/hora: {e}")
            self.datetime_configured = None
    
    def update_connection_status(self):
        """Actualiza el label de estado de conexión con información de fecha/hora"""
        if not hasattr(self, 'status_label'):
            return
        
        if self.ssh and self.ssh.isConnected:
            self.status_label.setText("✓ Conectada")
            self.status_label.setStyleSheet("color: green; font-size: 14px; font-weight: bold;")
            
            # Actualizar label de fecha/hora
            if hasattr(self, 'datetime_label') and self.datetime_configured:
                datetime_str = self.datetime_configured.strftime("%Y-%m-%d %H:%M:%S")
                self.datetime_label.setText(f"Fecha/Hora configurada: {datetime_str}")
                self.datetime_label.setStyleSheet("color: #27ae60; font-size: 11px;")
            elif hasattr(self, 'datetime_label'):
                self.datetime_label.setText("⚠ Fecha/hora no configurada")
                self.datetime_label.setStyleSheet("color: #e67e22; font-size: 11px;")
        else:
            self.status_label.setText("✗ Desconectada")
            self.status_label.setStyleSheet("color: red; font-size: 14px; font-weight: bold;")
            if hasattr(self, 'datetime_label'):
                self.datetime_label.setText("")
    
    def init_ui(self):
        """Inicializa la interfaz gráfica"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # === Área de Tabs ===
        tabs = QTabWidget()
        
        # Tab 1: Control de Datos
        data_control_tab = QWidget()
        data_control_layout = QHBoxLayout(data_control_tab)
        
        # Panel izquierdo: Controles
        controls_layout = QVBoxLayout()
        controls_layout.setSpacing(10)
        
        # === Sección: Estado de Conexión ===
        connection_status = QGroupBox("Conexión SSH")
        conn_layout = QVBoxLayout()
        
        # Label de estado de conexión
        status_text = "✓ Conectada" if (self.ssh and self.ssh.isConnected) else "✗ Desconectada"
        status_color = "green" if (self.ssh and self.ssh.isConnected) else "red"
        self.status_label = QLabel(status_text)
        self.status_label.setStyleSheet(f"color: {status_color}; font-size: 14px; font-weight: bold;")
        conn_layout.addWidget(self.status_label)
        
        # Label de fecha/hora configurada
        self.datetime_label = QLabel("")
        self.datetime_label.setStyleSheet("color: #2c3e50; font-size: 11px;")
        conn_layout.addWidget(self.datetime_label)
        
        # Actualizar con información de fecha/hora si ya está disponible
        self.update_connection_status()
        
        connection_status.setLayout(conn_layout)
        controls_layout.addWidget(connection_status)
        
        # === Sección: Debug Mode ===
        debug_group = QGroupBox("Debug Mode")
        debug_layout = QVBoxLayout()
        debug_label = QLabel("Seleccionar patrón de prueba o datos ADC:", font=QFont("Cantarell", 10))
        debug_layout.addWidget(debug_label)
        
        self.debug_combo = QComboBox(font=QFont("Cantarell", 10))
        for mode in config.DebugMode:
            self.debug_combo.addItem(mode.to_string(), mode.value)
        self.debug_combo.currentIndexChanged.connect(self.on_debug_changed)
        debug_layout.addWidget(self.debug_combo)
        debug_group.setLayout(debug_layout)
        controls_layout.addWidget(debug_group)
        
        # === Sección: Data Source ===
        data_source_group = QGroupBox("Data Source")
        data_source_layout = QVBoxLayout()
        data_source_label = QLabel("Fuente de datos de entrada al pipeline (ADC/Oscilador/Contador):", font=QFont("Cantarell", 10))
        data_source_layout.addWidget(data_source_label)
        
        self.data_source_combo = QComboBox(font=QFont("Cantarell", 10))
        for source in config.DataSource:
            self.data_source_combo.addItem(source.to_string(), source.value)
        self.data_source_combo.currentIndexChanged.connect(self.on_data_source_changed)
        data_source_layout.addWidget(self.data_source_combo)
        data_source_group.setLayout(data_source_layout)
        controls_layout.addWidget(data_source_group)
        
        # === Sección: FIFO Input ===
        fifo_group = QGroupBox("FIFO Input Mux")
        fifo_layout = QVBoxLayout()
        fifo_label = QLabel("Etapa del pipeline a capturar:", font=QFont("Cantarell", 10))
        fifo_layout.addWidget(fifo_label)
        
        self.fifo_combo = QComboBox(font=QFont("Cantarell", 10))
        for fifo in config.FIFOInput:
            self.fifo_combo.addItem(fifo.to_string(), fifo.value)
        self.fifo_combo.currentIndexChanged.connect(self.on_fifo_changed)
        fifo_layout.addWidget(self.fifo_combo)
        fifo_group.setLayout(fifo_layout)
        controls_layout.addWidget(fifo_group)
        
        # === Sección: Local Oscillator ===
        local_osc_group = QGroupBox("Local Oscillator Frequency")
        local_osc_layout = QVBoxLayout()
        local_osc_label = QLabel("Frecuencia oscilador local [MHz] (solo Data Source = Local Oscillator):", font=QFont("Utopia", 11, QFont.Bold))
        local_osc_layout.addWidget(local_osc_label)
        
        local_osc_h_layout = QHBoxLayout()
        self.local_osc_line_edit = QLineEdit(alignment=Qt.AlignCenter)
        self.local_osc_line_edit.setPlaceholderText("0.0 - 32.5")
        self.local_osc_line_edit.returnPressed.connect(self.apply_local_osc)
        local_osc_h_layout.addWidget(self.local_osc_line_edit, 1)
        
        self.local_osc_slider = QSlider(Qt.Horizontal)
        self.local_osc_slider.setMinimum(0)
        self.local_osc_slider.setMaximum(32500)
        self.local_osc_slider.setValue(10000)  # Default: 10 MHz
        self.local_osc_slider.valueChanged.connect(
            lambda: self.local_osc_line_edit.setText(f"{self.local_osc_slider.value()/1000:.3f}")
        )
        self.local_osc_slider.sliderReleased.connect(self.apply_local_osc)
        local_osc_h_layout.addWidget(self.local_osc_slider, 2)
        
        local_osc_layout.addLayout(local_osc_h_layout)
        local_osc_group.setLayout(local_osc_layout)
        controls_layout.addWidget(local_osc_group)
        
        # === Sección: Beam Frequencies ===
        beam_freq_group = QGroupBox("Final Mixer NCO (CH_MIXER)")
        beam_freq_layout = QVBoxLayout()
        
        # Selector de Beam (qué NCO es visible)
        beam_selector_layout = QHBoxLayout()
        beam_selector_label = QLabel("Beam Selector (visible en salida):", font=QFont("Cantarell", 10))
        beam_selector_layout.addWidget(beam_selector_label)
        self.beam_selector_combo = QComboBox()
        self.beam_selector_combo.addItems([f"Beam {i}" for i in range(5)])
        self.beam_selector_combo.setCurrentIndex(0)
        self.beam_selector_combo.currentIndexChanged.connect(self.set_beam_selector)
        beam_selector_layout.addWidget(self.beam_selector_combo)
        beam_selector_layout.addStretch()
        beam_freq_layout.addLayout(beam_selector_layout)
        beam_freq_layout.addSpacing(15)
        
        beam_freq_label = QLabel("Frecuencia NCO de mezcla final por canal [MHz]:", font=QFont("Utopia", 11, QFont.Bold))
        beam_freq_layout.addWidget(beam_freq_label)
        beam_freq_layout.addSpacing(10)
        
        self.beam_freq_setters = []
        for i in range(5):
            beam_label = QLabel(f"CH Mixer NCO {i}:", font=QFont("Cantarell", 10))
            beam_freq_layout.addWidget(beam_label)
            beam_setter = BeamFreqSetter(self, i)
            beam_freq_layout.addLayout(beam_setter.get_layout())
            beam_freq_layout.addSpacing(8)
            self.beam_freq_setters.append(beam_setter)
        
        beam_freq_group.setLayout(beam_freq_layout)
        controls_layout.addWidget(beam_freq_group)
        
        controls_layout.addStretch(1)
        
        # === Botones de Acción ===
        buttons_layout = QGridLayout()
        buttons_layout.setHorizontalSpacing(8)
        buttons_layout.setVerticalSpacing(8)
        
        # Botón SSH Connect/Disconnect
        self.ssh_btn = QPushButton("🔌 DESCONECTAR SSH")
        self.ssh_btn.setFont(QFont("Utopia", 11, QFont.Bold))
        self.update_ssh_button()
        self.ssh_btn.clicked.connect(self.toggle_ssh_connection)
        buttons_layout.addWidget(self.ssh_btn, 0, 0, 1, 2)
        
        # Botón Reset
        reset_btn = QPushButton("🔄 RESET System")
        reset_btn.setFont(QFont("Utopia", 12, QFont.Bold))
        reset_btn.setStyleSheet("background-color: #FF6B6B; color: white; padding: 10px;")
        reset_btn.clicked.connect(self.reset_system)
        buttons_layout.addWidget(reset_btn, 1, 0)

        # Botón Reboot placa
        reboot_btn = QPushButton("♻ REBOOT Board")
        reboot_btn.setFont(QFont("Utopia", 12, QFont.Bold))
        reboot_btn.setStyleSheet("background-color: #C0392B; color: white; padding: 10px;")
        reboot_btn.clicked.connect(self.reboot_board)
        buttons_layout.addWidget(reboot_btn, 1, 1)
        
        # Botón Enable/Disable (toggle)
        self.acquisition_btn = QPushButton("▶ ENABLE Acquisition")
        self.acquisition_btn.setFont(QFont("Utopia", 12, QFont.Bold))
        self.update_acquisition_button()
        self.acquisition_btn.clicked.connect(self.toggle_acquisition)
        buttons_layout.addWidget(self.acquisition_btn, 2, 0)
        
        # Botón Launch/Stop UDP Streaming (toggle)
        self.streaming_btn = QPushButton("🚀 LAUNCH UDP Streaming")
        self.streaming_btn.setFont(QFont("Utopia", 12, QFont.Bold))
        self.update_streaming_button()
        self.streaming_btn.clicked.connect(self.toggle_streaming)
        buttons_layout.addWidget(self.streaming_btn, 2, 1)
        
        # Botón Calibración IDELAY
        calibrate_btn = QPushButton("🔧 Calibrar IDELAY (startup.elf)")
        calibrate_btn.setFont(QFont("Utopia", 11, QFont.Bold))
        calibrate_btn.setStyleSheet("background-color: #F39C12; color: white; padding: 12px;")
        calibrate_btn.clicked.connect(self.execute_startup)
        buttons_layout.addWidget(calibrate_btn, 3, 0, 1, 2)
        
        controls_layout.addLayout(buttons_layout)
        
        data_control_layout.addLayout(controls_layout, 1)
        
        # Panel derecho: Consola SSH
        console_layout = QVBoxLayout()
        console_label = QLabel("Consola SSH (solo lectura):", font=QFont("Utopia", 11, QFont.Bold))
        console_layout.addWidget(console_label)
        
        self.ssh_console = QPlainTextEdit()
        self.ssh_console.setReadOnly(True)
        self.ssh_console.setFont(QFont("Courier", 9))
        self.ssh_console.setStyleSheet("background-color: #2C3E50; color: #ECF0F1;")
        console_layout.addWidget(self.ssh_console)
        
        # Campo de comandos manuales
        self.ssh_input = QLineEdit()
        self.ssh_input.setPlaceholderText("Comando manual SSH (opcional)")
        self.ssh_input.returnPressed.connect(lambda: textClickHandler(self, self.ssh_input))
        console_layout.addWidget(self.ssh_input)
        
        data_control_layout.addLayout(console_layout, 1)
        
        tabs.addTab(data_control_tab, "Control de Adquisición")
        
        # Tab 2: Configuraciones Presets
        presets_tab = QWidget()
        presets_layout = QVBoxLayout(presets_tab)
        presets_layout.setAlignment(Qt.AlignTop)
        
        presets_label = QLabel("Configuraciones Rápidas:", font=QFont("Utopia", 12, QFont.Bold))
        presets_layout.addWidget(presets_label)
        presets_layout.addSpacing(10)
        
        # Preset 1: Counter Test
        preset1_btn = QPushButton("🔢 Preset: Counter Test")
        preset1_btn.setFont(QFont("Cantarell", 11))
        preset1_btn.setMinimumHeight(50)
        preset1_btn.clicked.connect(lambda: self.apply_preset("counter"))
        presets_layout.addWidget(preset1_btn)
        
        preset1_desc = QLabel(
            "• Debug Mode: CONT_NBITS (0xF)\n"
            "• Data Source: CONTADOR\n"
            "• FIFO Input: MUX_DATA\n"
            "• Útil para validar desempaquetado UDP"
        )
        preset1_desc.setStyleSheet("margin-left: 20px; color: gray;")
        presets_layout.addWidget(preset1_desc)
        presets_layout.addSpacing(15)
        
        # Preset 2: ADC Raw
        preset2_btn = QPushButton("📡 Preset: ADC Raw Data")
        preset2_btn.setFont(QFont("Cantarell", 11))
        preset2_btn.setMinimumHeight(50)
        preset2_btn.clicked.connect(lambda: self.apply_preset("adc_raw"))
        presets_layout.addWidget(preset2_btn)
        
        preset2_desc = QLabel(
            "• Debug Mode: DISABLED (0x0)\n"
            "• Data Source: DATOS_ADC\n"
            "• FIFO Input: RAW_DATA\n"
            "• Datos directos de ADC sin procesamiento"
        )
        preset2_desc.setStyleSheet("margin-left: 20px; color: gray;")
        presets_layout.addWidget(preset2_desc)
        presets_layout.addSpacing(15)
        
        # Preset 3: Preprocessed
        preset3_btn = QPushButton("⚙️ Preset: Preprocessed Data")
        preset3_btn.setFont(QFont("Cantarell", 11))
        preset3_btn.setMinimumHeight(50)
        preset3_btn.clicked.connect(lambda: self.apply_preset("preprocessed"))
        presets_layout.addWidget(preset3_btn)
        
        preset3_desc = QLabel(
            "• Debug Mode: DISABLED (0x0)\n"
            "• Data Source: DATOS_ADC\n"
            "• FIFO Input: PREPROC_DATA\n"
            "• Con beamforming y filtrado"
        )
        preset3_desc.setStyleSheet("margin-left: 20px; color: gray;")
        presets_layout.addWidget(preset3_desc)
        
        presets_layout.addStretch(1)
        
        tabs.addTab(presets_tab, "Presets")
        
        main_layout.addWidget(tabs)
    
    # === Métodos de Configuración ===
    
    def on_debug_changed(self):
        """Handler para cambio de Debug Mode"""
        value = self.debug_combo.currentData()
        cmds = config.set_debug_mode_all_channels_cmds(value)
        for cmd in cmds:
            self.write_ssh(cmd)
        self.log_message(f"Debug Mode aplicado a {len(cmds)} canales (valor=0x{value:X})")

    def set_combo_to_value(self, combo, value):
        """Setea un QComboBox según el valor real asociado (UserData)."""
        index = combo.findData(value)
        if index >= 0:
            combo.setCurrentIndex(index)
    
    def on_data_source_changed(self):
        """Handler para cambio de Data Source"""
        value = self.data_source_combo.currentData()
        cmd = config.set_data_source_cmd(value)
        self.write_ssh(cmd)
    
    def on_fifo_changed(self):
        """Handler para cambio de FIFO Input"""
        value = self.fifo_combo.currentData()
        cmd = config.set_fifo_input_cmd(value)
        self.write_ssh(cmd)
    
    def apply_local_osc(self):
        """Aplica configuración de oscilador local"""
        try:
            freq = float(self.local_osc_line_edit.text())
            cmd = config.set_local_osc_freq_cmd(freq)
            self.write_ssh(cmd)
        except ValueError:
            self.log_message("ERROR: Frecuencia de oscilador local inválida")
    
    def toggle_ssh_connection(self):
        """Conectar o desconectar SSH"""
        if self.ssh and self.ssh.isConnected:
            # Desconectar
            reply = QMessageBox.question(
                self,
                'Desconectar SSH',
                '¿Desea desconectar la sesión SSH?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                try:
                    self.ssh.ssh.close()
                    self.ssh = None
                    self.datetime_configured = None
                    self.streaming_active = False
                    print("✗ Desconectado de CIAA")
                    self.log_message("=== SSH DESCONECTADO ===")
                    self.update_ssh_button()
                    self.update_connection_status()
                    self.update_streaming_button()
                except Exception as e:
                    self.log_message(f"ERROR al desconectar: {e}", is_error=True)
        else:
            # Conectar
            self.connect_ssh()
            self.update_ssh_button()
            self.update_connection_status()
    
    def toggle_acquisition(self):
        """Toggle entre Enable/Disable acquisition"""
        if not self.ssh or not self.ssh.isConnected:
            self.log_message("ERROR: No hay conexión SSH", is_error=True)
            return
        
        self.acquisition_enabled = not self.acquisition_enabled
        
        if self.acquisition_enabled:
            self.write_ssh(config.enable_cmd(True))
            self.log_message("=== ACQUISITION ENABLED ===")
        else:
            self.write_ssh(config.enable_cmd(False))
            self.log_message("=== ACQUISITION DISABLED ===")
        
        self.update_acquisition_button()
    
    def toggle_streaming(self):
        """Toggle entre Launch/Stop UDP streaming"""
        if not self.ssh or not self.ssh.isConnected:
            self.log_message("ERROR: No hay conexión SSH", is_error=True)
            return
        
        if self.streaming_active:
            # Detener streaming
            reply = QMessageBox.question(
                self,
                'Detener Streaming',
                '¿Desea detener el streaming UDP?\n\nSe ejecutará: killall sist_adq_crc.elf',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                cmd = 'killall sist_adq_crc.elf'
                self.write_ssh(cmd)
                self.streaming_active = False
                self.log_message("=== UDP STREAMING DETENIDO ===")
                self.update_streaming_button()
        else:
            # Iniciar streaming
            reply = QMessageBox.question(
                self,
                'Lanzar UDP Streaming',
                'Se iniciará el servidor UDP en CIAA en modo background.\n'
                'NOTA: Asegúrese de haber configurado client_config_udp en /mnt/currentVersions/\n\n'
                '¿Continuar?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                # Usar nohup para ejecutar en background sin bloquear SSH
                cmd = 'cd /mnt/currentVersions && nohup ./sist_adq_crc.elf client_config_udp > /tmp/udp_stream.log 2>&1 &'
                self.write_ssh(cmd)
                self.streaming_active = True
                self.log_message("=== UDP STREAMING INICIADO (background) ===\nLogs: /tmp/udp_stream.log en CIAA")
                self.update_streaming_button()
    
    def update_ssh_button(self):
        """Actualiza el botón SSH según el estado de conexión"""
        if hasattr(self, 'ssh_btn'):
            if self.ssh and self.ssh.isConnected:
                self.ssh_btn.setText("🔌 DESCONECTAR SSH")
                self.ssh_btn.setStyleSheet("background-color: #E67E22; color: white; padding: 10px;")
            else:
                self.ssh_btn.setText("🔌 CONECTAR SSH")
                self.ssh_btn.setStyleSheet("background-color: #3498DB; color: white; padding: 10px;")
    
    def update_acquisition_button(self):
        """Actualiza el botón de acquisition según el estado"""
        if hasattr(self, 'acquisition_btn'):
            if self.acquisition_enabled:
                self.acquisition_btn.setText("⏸ DISABLE Acquisition")
                self.acquisition_btn.setStyleSheet("background-color: #95A5A6; color: white; padding: 10px;")
            else:
                self.acquisition_btn.setText("▶ ENABLE Acquisition")
                self.acquisition_btn.setStyleSheet("background-color: #4ECDC4; color: white; padding: 10px;")
    
    def update_streaming_button(self):
        """Actualiza el botón de streaming según el estado"""
        if hasattr(self, 'streaming_btn'):
            if self.streaming_active:
                self.streaming_btn.setText("⏹ STOP UDP Streaming")
                self.streaming_btn.setStyleSheet("background-color: #E74C3C; color: white; padding: 15px;")
            else:
                self.streaming_btn.setText("🚀 LAUNCH UDP Streaming")
                self.streaming_btn.setStyleSheet("background-color: #2ECC71; color: white; padding: 15px;")
    
    def reset_system(self):
        """Reset asíncrono + FIFO reset"""
        self.write_ssh(config.reset_async_cmd())
        self.write_ssh(config.reset_fifo_cmd())
        self.log_message("=== RESET COMPLETO ===")
    
    def execute_startup(self):
        """Ejecuta startup.elf (calibración IDELAY)"""
        cmd = config.startup_cmd()
        self.write_ssh(cmd)
        self.log_message("=== EJECUTANDO STARTUP.ELF (IDELAY calibration) ===\nESPERE 10-15 segundos...")

    def reboot_board(self):
        """Reinicia la placa via comando reboot en Linux."""
        if not self.ssh or not self.ssh.isConnected:
            self.log_message("ERROR: No hay conexión SSH", is_error=True)
            return

        reply = QMessageBox.question(
            self,
            'Reiniciar Placa',
            '¿Desea reiniciar la placa CIAA?\n\nSe ejecutará: reboot\nLa conexión SSH se perderá temporalmente.',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.write_ssh(config.reboot_cmd())
            self.streaming_active = False
            self.acquisition_enabled = False
            self.update_streaming_button()
            self.update_acquisition_button()
            self.log_message("=== REBOOT ENVIADO A LA PLACA ===")
    
    def set_beam_selector(self, beam_index):
        """Selecciona qué NCO de canal (0-4) es visible en la salida"""
        if not self.ssh or not self.ssh.isConnected:
            self.log_message("ERROR: No hay conexión SSH", is_error=True)
            return
        
        cmd = config.set_beam_selector_cmd(beam_index)
        self.write_ssh(cmd)
        self.log_message(f"Beam Selector = {beam_index} (NCO {beam_index} visible en salida)")
    
    def apply_preset(self, preset_name):
        """Aplica configuración predefinida"""
        self.log_message(f"\n{'='*50}\nAplicando preset: {preset_name.upper()}\n{'='*50}")
        
        if preset_name == "counter":
            self.reset_system()
            self.set_combo_to_value(self.debug_combo, config.DebugMode.CONT_NBITS.value)
            self.set_combo_to_value(self.data_source_combo, config.DataSource.CONTADOR.value)
            self.set_combo_to_value(self.fifo_combo, config.FIFOInput.MUX_DATA.value)
            # Enable si no está habilitado
            if not self.acquisition_enabled:
                self.toggle_acquisition()
        
        elif preset_name == "adc_raw":
            self.reset_system()
            self.set_combo_to_value(self.debug_combo, config.DebugMode.DISABLED.value)
            self.set_combo_to_value(self.data_source_combo, config.DataSource.DATOS_ADC.value)
            self.set_combo_to_value(self.fifo_combo, config.FIFOInput.RAW_DATA.value)
            # Enable si no está habilitado
            if not self.acquisition_enabled:
                self.toggle_acquisition()
        
        elif preset_name == "preprocessed":
            self.reset_system()
            self.set_combo_to_value(self.debug_combo, config.DebugMode.DISABLED.value)
            self.set_combo_to_value(self.data_source_combo, config.DataSource.DATOS_ADC.value)
            self.set_combo_to_value(self.fifo_combo, config.FIFOInput.PREPROC_DATA.value)
            # Enable si no está habilitado
            if not self.acquisition_enabled:
                self.toggle_acquisition()
        
        self.log_message(f"Preset '{preset_name}' aplicado correctamente.\n")
    
    # === Utilidades SSH ===
    
    def write_ssh(self, cmd):
        """Ejecuta comando SSH y muestra resultado"""
        if not self.ssh or not self.ssh.isConnected:
            self.log_message("ERROR: No hay conexión SSH")
            return
        
        try:
            stdin, stdout, stderr = self.ssh.execute(cmd)
            
            # Log comando
            self.log_message(f"> {cmd}")
            
            # Log salida
            for line in stdout:
                self.log_message(line.strip())
            
            # Log errores
            for line in stderr:
                self.log_message(f"ERROR: {line.strip()}", is_error=True)
        
        except Exception as e:
            self.log_message(f"ERROR SSH: {e}", is_error=True)
    
    def log_message(self, message, is_error=False):
        """Agrega mensaje a la consola"""
        if is_error:
            self.ssh_console.appendHtml(f'<span style="color: #E74C3C;">{message}</span>')
        else:
            self.ssh_console.appendPlainText(message)
    
    def closeEvent(self, event):
        """Maneja cierre de ventana"""
        # Preguntar si detener streaming si está activo
        if self.streaming_active and self.ssh and self.ssh.isConnected:
            reply_stream = QMessageBox.question(
                self,
                'Streaming Activo',
                '¿Desea detener el proceso sist_adq_crc.elf antes de salir?',
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Yes
            )
            
            if reply_stream == QMessageBox.Cancel:
                event.ignore()
                return
            elif reply_stream == QMessageBox.Yes:
                try:
                    cmd = 'killall sist_adq_crc.elf'
                    self.write_ssh(cmd)
                    self.log_message("=== UDP STREAMING DETENIDO ===")
                except Exception as e:
                    print(f"Error al detener streaming: {e}")
        
        # Confirmar cierre
        reply = QMessageBox.question(
            self,
            'Cerrar Aplicación',
            '¿Seguro que desea salir?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.ssh:
                try:
                    self.ssh.ssh.close()
                except:
                    pass
            event.accept()
        else:
            event.ignore()


if __name__ == '__main__':
    # Crear QApplication (o reusar existente si estamos en Spyder/IPython)
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    window = MainWindow()
    window.show()
    
    # Si estamos en un entorno interactivo (Spyder), no llamar exec_()
    # porque bloquearía el kernel
    if app.instance() is not None:
        # Entorno interactivo: la ventana se muestra pero no bloquea
        try:
            from IPython import get_ipython
            if get_ipython() is not None:
                # Estamos en IPython/Spyder - no bloquear
                print("UI iniciada en modo interactivo (Spyder)")
            else:
                # Terminal normal
                sys.exit(app.exec_())
        except ImportError:
            # No hay IPython, ejecutar normalmente
            sys.exit(app.exec_())
    else:
        sys.exit(app.exec_())
