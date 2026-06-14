# Parte 2 - Contador concorrente com semaforo
import threading
import time
import struct

T = 8          # numero de threads (minimo 8 conforme enunciado)
M = 200_000    # incrementos por thread (minimo 200.000 conforme enunciado)
ESPERADO = T * M

# ── versao 1: sem sincronizacao (race condition) ──────────────────────────────

def fazer_buf():
    return bytearray(8)

def ler(buf):
    return struct.unpack_from('<q', buf, 0)[0]

def escrever(buf, v):
    struct.pack_into('<q', buf, 0, v)

buf_inseguro = fazer_buf()

def tarefa_sem_sync():
    for _ in range(M):
        # leitura e escrita separadas: nao atomicas com o GIL
        # outra thread pode escrever entre o ler() e o escrever()
        escrever(buf_inseguro, ler(buf_inseguro) + 1)

def rodar_sem_sync():
    escrever(buf_inseguro, 0)
    threads = [threading.Thread(target=tarefa_sem_sync) for _ in range(T)]
    t0 = time.time()
    for t in threads: t.start()
    for t in threads: t.join()
    return ler(buf_inseguro), time.time() - t0


# ── versao 2: com semaforo binario (correta) ──────────────────────────────────

buf_seguro = fazer_buf()
sem = threading.Semaphore(1)  # semaforo binario (1 permissao = exclusao mutua)

def tarefa_com_sem():
    for _ in range(M):
        sem.acquire()
        try:
            escrever(buf_seguro, ler(buf_seguro) + 1)
        finally:
            sem.release()
        # release() estabelece barreira de memoria implicita em Python:
        # o valor atualizado e visivel para a proxima thread que fizer acquire()
        # (equivalente ao happens-before do Java)

def rodar_com_sem():
    escrever(buf_seguro, 0)
    threads = [threading.Thread(target=tarefa_com_sem) for _ in range(T)]
    t0 = time.time()
    for t in threads: t.start()
    for t in threads: t.join()
    return ler(buf_seguro), time.time() - t0


# ── execucao e tabela ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"Configuracao: T={T} threads, M={M} incrementos/thread, esperado={ESPERADO:,}\n")
    print("Rodando 3 execucoes de cada versao...\n")

    resultados_inseguro = []
    resultados_seguro = []

    for i in range(1, 4):
        val, tempo = rodar_sem_sync()
        resultados_inseguro.append((val, tempo))
        print(f"[sem sync #{i}] obtido={val:,}  perdidos={ESPERADO-val:,}  tempo={tempo:.4f}s")

    print()

    for i in range(1, 4):
        val, tempo = rodar_com_sem()
        resultados_seguro.append((val, tempo))
        print(f"[com sem  #{i}] obtido={val:,}  correto={val == ESPERADO}  tempo={tempo:.4f}s")

    print("\n=== TABELA DE RESULTADOS ===")
    print(f"{'Versao':<15} {'Exec':<6} {'Esperado':>12} {'Obtido':>12} {'Perdidos':>12} {'Tempo(s)':>10}")
    print("-" * 68)
    for i, (val, t) in enumerate(resultados_inseguro, 1):
        print(f"{'Sem sync':<15} {'#'+str(i):<6} {ESPERADO:>12,} {val:>12,} {ESPERADO-val:>12,} {t:>10.4f}")
    print("-" * 68)
    for i, (val, t) in enumerate(resultados_seguro, 1):
        print(f"{'Com semaforo':<15} {'#'+str(i):<6} {ESPERADO:>12,} {val:>12,} {0:>12,} {t:>10.4f}")

    media_sem = sum(t for _, t in resultados_inseguro) / 3
    media_com = sum(t for _, t in resultados_seguro) / 3
    print(f"\nMedia sem sync:  {media_sem:.4f}s")
    print(f"Media com sem:   {media_com:.4f}s")
    print(f"Overhead do sem: {media_com/media_sem:.1f}x mais lento")
