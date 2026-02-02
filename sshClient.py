import paramiko
import re

class ShellHandler:
    """
    Cliente SSH para CIAA-ACC (192.168.0.22)
    Mantiene sesión shell interactiva persistente.
    """
    
    def __init__(self):
        self.isConnected = False
        self.ssh = paramiko.SSHClient()
        try:
            self.ssh.connect('192.168.0.22', username='root', password=None, timeout=3)
            self.isConnected = True
        except Exception as _:
            try:
                self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self.ssh.get_transport().auth_none('root')
                self.isConnected = True
            except Exception as _:
                self.isConnected = False
                return

        channel = self.ssh.invoke_shell()
        self.stdin = channel.makefile('wb')
        self.stdout = channel.makefile('r')

    def __del__(self):
        try:
            self.ssh.close()
        except:
            pass

    def execute(self, cmd):
        """
        Ejecuta comando en la CIAA y retorna resultado
        
        :param cmd: Comando a ejecutar
        :return: (stdin, stdout_lines, stderr_lines)
        """
        cmd = cmd.strip('\n')
        self.stdin.write(cmd + '\n')
        finish = 'end of stdOUT buffer. finished with exit status'
        echo_cmd = 'echo {} $?'.format(finish)
        self.stdin.write(echo_cmd + '\n')
        shin = self.stdin
        self.stdin.flush()

        shout = []
        sherr = []
        exit_status = 0
        
        for line in self.stdout:
            if str(line).startswith(cmd) or str(line).startswith(echo_cmd):
                # Limpiar buffer de shell junk
                shout = []
            elif str(line).startswith(finish):
                # Comando terminó con exit status
                exit_status = int(str(line).rsplit(maxsplit=1)[1])
                if exit_status:
                    # Si hay error, stdout pasa a stderr
                    sherr = shout
                    shout = []
                break
            else:
                # Remover caracteres ANSI de formato/color
                clean_line = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]').sub('', line)
                clean_line = clean_line.replace('\b', '').replace('\r', '')
                shout.append(clean_line)

        # Remover líneas de prompt al inicio y final
        if shout and echo_cmd in shout[-1]:
            shout.pop()
        if shout and cmd in shout[0]:
            shout.pop(0)
        if sherr and echo_cmd in sherr[-1]:
            sherr.pop()
        if sherr and cmd in sherr[0]:
            sherr.pop(0)

        return shin, shout, sherr


if __name__ == '__main__':
    # Modo standalone: cliente SSH interactivo
    shell = ShellHandler()
    if not shell.isConnected:
        print('✗ No se pudo conectar a CIAA (192.168.0.22)')
        exit(1)
    
    print('✓ Conectado a CIAA')
    print('Escriba comandos (Ctrl+C para salir):\n')
    
    try:
        while True:
            cmd = input('ciaa> ')
            if cmd.strip():
                _, stdout, stderr = shell.execute(cmd)
                for line in stdout:
                    print(line.strip())
                for line in stderr:
                    print(f'ERROR: {line.strip()}')
    except KeyboardInterrupt:
        print('\n✓ Desconectado')
