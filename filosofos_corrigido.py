# Parte 1 - Jantar dos Filosofos (versao CORRIGIDA - hierarquia de recursos)
import threading
import time
import random

N = 5
CICLOS = 5

garfos = [threading.Semaphore(1) for _ in range(N)]
estado = ["pensando"] * N
refeicoes = [0] * N
lock_print = threading.Lock()

def log(p, msg):
    with lock_print:
        print(f"[Filosofo {p}] {msg}  | estados: {estado}")

def filosofo(p):
    esq = p
    dir = (p + 1) % N

    # hierarquia: sempre pega o garfo de menor indice primeiro
    # isso quebra a espera circular (condicao 4 de Coffman)
    primeiro = min(esq, dir)
    segundo = max(esq, dir)

    for i in range(CICLOS):
        # pensando
        estado[p] = "pensando"
        log(p, f"pensando... (ciclo {i+1}/{CICLOS})")
        time.sleep(random.uniform(0.3, 0.8))

        # com fome
        estado[p] = "com fome"
        log(p, f"com fome, quer garfos {primeiro} e {segundo}")

        garfos[primeiro].acquire()
        log(p, f"pegou garfo {primeiro}, aguardando garfo {segundo}...")
        garfos[segundo].acquire()

        # comendo
        estado[p] = "comendo"
        log(p, f"COMENDO (ciclo {i+1}/{CICLOS})")
        time.sleep(random.uniform(0.2, 0.5))

        garfos[segundo].release()
        garfos[primeiro].release()

        refeicoes[p] += 1

    estado[p] = "pensando"
    log(p, f"terminou! total de refeicoes: {refeicoes[p]}")


if __name__ == "__main__":
    print("=== VERSAO CORRIGIDA (hierarquia de recursos, sem deadlock) ===\n")

    threads = [threading.Thread(target=filosofo, args=(i,), name=f"F{i}") for i in range(N)]
    inicio = time.time()
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print(f"\ntempo total: {time.time()-inicio:.2f}s")
    print(f"refeicoes por filosofo: {refeicoes}")
    print(f"total: {sum(refeicoes)} (esperado: {N * CICLOS})")
