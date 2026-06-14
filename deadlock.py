# Parte 3 - Deadlock: reproducao e correcao
# Matheus Murbach, Guilherme Mendonça, João Gabriel, Gustavo Arcanjelo

import threading
import time
import sys

LOCK_A = threading.Lock()
LOCK_B = threading.Lock()

# ── versao que TRAVA (deadlock classico) ─────────────────────────────────────

def thread1_deadlock():
    print("[T1] adquirindo LOCK_A...")
    LOCK_A.acquire()
    print("[T1] adquiriu LOCK_A. Dormindo 50ms...")
    time.sleep(0.05)  # aumenta chance do deadlock (T2 pega LOCK_B nesse intervalo)
    print("[T1] tentando LOCK_B... (vai travar se T2 ja pegou)")
    LOCK_B.acquire()
    print("[T1] concluiu")  # nunca chega aqui em deadlock
    LOCK_B.release()
    LOCK_A.release()

def thread2_deadlock():
    print("[T2] adquirindo LOCK_B...")
    LOCK_B.acquire()
    print("[T2] adquiriu LOCK_B. Dormindo 50ms...")
    time.sleep(0.05)
    print("[T2] tentando LOCK_A... (vai travar se T1 ja pegou)")
    LOCK_A.acquire()
    print("[T2] concluiu")  # nunca chega aqui em deadlock
    LOCK_A.release()
    LOCK_B.release()


def diagnostico_deadlock():
    """mostra quais threads estao bloqueadas (equivalente ao jstack do Java)"""
    print("\n=== DIAGNOSTICO DE THREADS (threading.enumerate) ===")
    for t in threading.enumerate():
        print(f"  thread: {t.name} | alive: {t.is_alive()} | daemon: {t.daemon}")
    print("=== FIM DO DIAGNOSTICO ===\n")


def demo_deadlock():
    print("=" * 55)
    print("VERSAO QUE TRAVA (deadlock)")
    print("=" * 55)
    print("T1 pega LOCK_A depois tenta LOCK_B")
    print("T2 pega LOCK_B depois tenta LOCK_A")
    print("=> espera circular => deadlock\n")

    t1 = threading.Thread(target=thread1_deadlock, name="Thread-1", daemon=True)
    t2 = threading.Thread(target=thread2_deadlock, name="Thread-2", daemon=True)

    t1.start()
    t2.start()

    t1.join(timeout=3)
    t2.join(timeout=3)

    if t1.is_alive() or t2.is_alive():
        print("\n*** DEADLOCK CONFIRMADO: programa travado ***")
        diagnostico_deadlock()
        print("Condicoes de Coffman presentes:")
        print("  1. Exclusao mutua: LOCK_A e LOCK_B sao locks binarios")
        print("  2. Manter-e-esperar: T1 segura LOCK_A enquanto espera LOCK_B")
        print("  3. Nao preempcao: nenhuma thread libera o lock voluntariamente")
        print("  4. Espera circular: T1 -> aguarda T2 -> aguarda T1")
    else:
        print("\nNao travou dessa vez (escalonamento favoravel)")


# ── versao CORRIGIDA (hierarquia: sempre LOCK_A antes de LOCK_B) ─────────────

LOCK_A2 = threading.Lock()
LOCK_B2 = threading.Lock()
concluidos = []
lock_c = threading.Lock()

def thread1_corrigido():
    # hierarquia: sempre LOCK_A primeiro
    print("[T1] adquirindo LOCK_A...")
    LOCK_A2.acquire()
    print("[T1] adquiriu LOCK_A. Tentando LOCK_B...")
    time.sleep(0.05)
    LOCK_B2.acquire()
    print("[T1] adquiriu LOCK_B. Secao critica OK.")
    time.sleep(0.1)
    LOCK_B2.release()
    LOCK_A2.release()
    print("[T1] concluiu e liberou os locks")
    with lock_c:
        concluidos.append("T1")

def thread2_corrigido():
    # mesma hierarquia: sempre LOCK_A primeiro (antes era LOCK_B primeiro)
    print("[T2] adquirindo LOCK_A...")
    LOCK_A2.acquire()
    print("[T2] adquiriu LOCK_A. Tentando LOCK_B...")
    time.sleep(0.05)
    LOCK_B2.acquire()
    print("[T2] adquiriu LOCK_B. Secao critica OK.")
    time.sleep(0.1)
    LOCK_B2.release()
    LOCK_A2.release()
    print("[T2] concluiu e liberou os locks")
    with lock_c:
        concluidos.append("T2")


def demo_corrigido():
    print("=" * 55)
    print("VERSAO CORRIGIDA (hierarquia de recursos)")
    print("=" * 55)
    print("Regra: TODAS as threads adquirem LOCK_A antes de LOCK_B")
    print("=> espera circular impossivel => sem deadlock\n")

    t1 = threading.Thread(target=thread1_corrigido, name="Thread-1")
    t2 = threading.Thread(target=thread2_corrigido, name="Thread-2")

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    print(f"\nAmbas concluiram! Ordem: {concluidos}")
    print("Condicao de Coffman quebrada: espera circular (condicao 4)")
    print("Como: impondo ordem global LOCK_A < LOCK_B, nenhum ciclo de")
    print("espera pode se formar entre as threads.")


# ── main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    demo_deadlock()
    print()
    demo_corrigido()
