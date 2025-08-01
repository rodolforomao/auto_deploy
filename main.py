import paramiko
import time
import os
from datetime import datetime
from dotenv import load_dotenv
import os
base_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv()

def ssh_git_pull():
    ssh_host = os.getenv('SSH_HOST')
    ssh_user = os.getenv('SSH_USER')
    ssh_password = os.getenv('SSH_PASSWORD')

    if not all([ssh_host, ssh_user, ssh_password]):
        print("[ERRO] Variáveis SSH não encontradas ou incompletas no .env.")
        return

    # Lê os pares GIT_PATH_n e GIT_PASS_n
    git_targets = []
    index = 1
    while True:
        path_key = 'GIT_PATH_' + str(index)
        pass_key = 'GIT_PASS_' + str(index)
        git_path = os.getenv(path_key)
        git_pass = os.getenv(pass_key)
        if git_path and git_pass:
            git_targets.append((git_path, git_pass))
            index += 1
        else:
            break

    if not git_targets:
        print("[ERRO] Nenhum par GIT_PATH_n / GIT_PASS_n encontrado no .env.")
        return

    try:
        # Conectar via SSH
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ssh_host, username=ssh_user, password=ssh_password)

        shell = client.invoke_shell()
        time.sleep(1)

        def wait_for(prompt, timeout=10):
            buffer = ''
            start_time = time.time()
            while time.time() - start_time < timeout:
                if shell.recv_ready():
                    data = shell.recv(1024).decode('utf-8', 'ignore')
                    buffer += data
                    if prompt in buffer:
                        return buffer
                time.sleep(0.1)
            raise Exception("Timeout esperando por: '" + prompt + "'")

        def send_command(cmd, wait_for_prompt=None, delay=1):
            shell.send(cmd + '\n')
            time.sleep(delay)
            if wait_for_prompt:
                return wait_for(wait_for_prompt)
            return ""

        # Entrar como root
        send_command('sudo su')
        wait_for("password for")
        send_command(ssh_password, delay=2)

        # Executar git pull para cada diretório
        for i in range(len(git_targets)):
            git_path, git_pass = git_targets[i]
            print("🔁 Atualizando: " + git_path)
            send_command("git -C '" + git_path + "' pull origin master")
            wait_for("password:", timeout=5)
            send_command(git_pass, delay=3)
            time.sleep(2)
            output = ""
            if shell.recv_ready():
                output = shell.recv(4096).decode('utf-8', 'ignore')
            else:
                output = "Nenhuma saída recebida."

            # Salva a saída em arquivo .log
            safe_name = git_path.strip("/").replace("/", "_")
            #log_file = "git_pull_" + safe_name + ".log"
            log_file = os.path.join(base_dir, "git_pull_" + safe_name + ".log")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(log_file, "w") as f:
                f.write("Data e hora: " + timestamp + "\n")
                f.write("Log do repositório: " + git_path + "\n")
                f.write(output)
                f.write("\n\n")
            print(output)

        # Sair da sessão
        send_command('exit')
        send_command('exit')
        client.close()

        print("\n✅ Todos os pull foram executados. Logs salvos como git_pull_<nome>.log")

    except Exception as e:
        print("[ERRO] " + str(e))

if __name__ == "__main__":
    ssh_git_pull()
