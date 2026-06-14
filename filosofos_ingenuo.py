# Parte 1 - Jantar dos Filosofos (versao INGENUA - entra em deadlock)
# Matheus Murbach, Guilherme Mendonça, João Gabriel, Gustavo Arcanjelo

import threading
import time

N = 5
# semaforos para os garfos
garfos = [threading.Semaphore(1) for _ in range(N)]
estado = ["pensando"] * N
lock_print = threading.Lock()

def log(p, msg):
    with lock_print:
        print(f"[Filosofo {p}] {msg}  | estados: {estado}")

def filosofo_ingenuo(p):
    left = p
    right = (p + 1) % N

    # protocolo ingenuo: sempre pega esquerdo antes de direito, sem hierarquia
    # se todos pegarem o garfo esquerdo simultaneamente => deadlock garantido

    estado[p] = "com fome"
    log(p, f"com fome, pegando garfo esquerdo {left}...")
    garfos[left].acquire()
    log(p, f"pegou garfo {left}. Aguardando garfo direito {right}...")

    # sleep garante que TODOS os filosofos peguem o garfo esquerdo
    # antes de qualquer um tentar o direito => deadlock deterministico
    time.sleep(0.5)

    log(p, f"tentando garfo {right}... (TRAVADO se outro filosofo ja pegou)")
    garfos[right].acquire()  # bloqueia aqui para sempre em deadlock

    estado[p] = "comendo"
    log(p, "comendo!")  # nunca chega aqui
    garfos[right].release()
    garfos[left].release()


if __name__ == "__main__":
    print("=== VERSAO INGENUA (deadlock garantido) ===")
    print("Todos os filosofos pegam o garfo esquerdo primeiro.")
    print("Apos 0.5s todos tentam o direito => espera circular => deadlock.\n")

    threads = []
    for i in range(N):
        t = threading.Thread(target=filosofo_ingenuo, args=(i,), name=f"F{i}", daemon=True)
        threads.append(t)

    for t in threads:
        t.start()

    # aguarda tempo suficiente para o deadlock se manifestar
    for t in threads:
        t.join(timeout=3)

    travados = [t for t in threads if t.is_alive()]
    print(f"\n*** DEADLOCK: {len(travados)}/{N} filosofos travados permanentemente ***")
    print("\nDiagnostico das threads (equivalente ao jstack do Java):")
    for t in threading.enumerate():
        print(f"  {t.name}: alive={t.is_alive()}, daemon={t.daemon}")

    print("\nCondicoes de Coffman presentes:")
    print("  1. Exclusao mutua: cada garfo so pode ser usado por 1 filosofo")
    print("  2. Manter-e-esperar: cada filosofo segura 1 garfo enquanto espera o outro")
    print("  3. Nao preempcao: nenhum filosofo larga o garfo que ja tem")
    print("  4. Espera circular: F0->F1->F2->F3->F4->F0 (cada um espera o vizinho)")
