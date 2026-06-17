# TDE — Filósofos, Semáforos e Deadlock

**Integrantes:** Matheus Murbach, Guilherme Ferreira, João Gabriel, Gustavo Arcanjelo  

**Grupo:** Grupo TDE 8

**Linguagem:** Python

**Vídeo:** [https://youtu.be/9dpt8XlJLdY]

**Repositório GitHub:** [https://github.com/Matheus-0103/TDE-II.git]
---

## Parte 1 — Jantar dos Filósofos

5 filósofos numa mesa circular, cada um precisa de 2 garfos pra comer (o da esquerda e o da direita). O problema é que os garfos são compartilhados com os vizinhos, então tem que ter algum controle de quem pega o quê e quando.

Cada filósofo passa por 3 estados: **pensando**, **com fome** e **comendo**.

### Por que o protocolo ingênuo trava

No protocolo ingênuo todos pegam o garfo da esquerda primeiro. Colocamos um `sleep(0.5s)` entre pegar o esquerdo e tentar o direito — isso garante que todos os 5 filósofos pegam o garfo esquerdo antes de qualquer um tentar o direito. Aí nenhum consegue o segundo garfo porque o vizinho já pegou, e todo mundo fica esperando pra sempre. Isso é deadlock.

As 4 condições de Coffman aparecem todas ao mesmo tempo:
1. exclusão mútua — cada garfo só pode ser usado por um filósofo
2. manter-e-esperar — cada um segura um garfo enquanto espera o outro
3. sem preempção — ninguém solta o garfo que já tem
4. espera circular — F0 espera F1, F1 espera F2... F4 espera F0

### Pseudocódigo ingênuo (causa o deadlock)

```
para cada filósofo p:
    left  = p
    right = (p + 1) mod N

    loop:
        pensar()
        estado[p] = "com fome"
        adquirir(left)     // todos pegam o esquerdo
        dormir(500ms)      // nesse tempo todos ficam com 1 garfo
        adquirir(right)    // todos bloqueiam aqui => deadlock
```

### Solução: hierarquia de recursos

A correção foi atribuir um índice pra cada garfo e fazer todo mundo pegar sempre o de menor índice primeiro. Isso quebra a espera circular (condição 4 de Coffman) porque não tem como formar um ciclo se todo mundo segue a mesma ordem.

O filósofo 4 por exemplo tem os garfos 4 e 0. Sem hierarquia ele pegaria o 4 primeiro, fechando o ciclo. Com a hierarquia ele pega o 0 primeiro, que é o mesmo que o filósofo 0 quer — aí um dos dois bloqueia antes de criar o problema.

### Pseudocódigo corrigido

```
para cada filósofo p:
    primeiro = min(garfo_esq(p), garfo_dir(p))
    segundo  = max(garfo_esq(p), garfo_dir(p))

    loop:
        pensar()
        estado[p] = "com fome"
        adquirir(primeiro)
        adquirir(segundo)
        estado[p] = "comendo"
        comer()
        liberar(segundo)
        liberar(primeiro)
        estado[p] = "pensando"
```

### Progresso e justiça

Com a hierarquia sempre pelo menos um filósofo consegue os dois garfos e come. Depois ele libera tudo imediatamente, então os vizinhos conseguem progredir também. Os tempos de pensar e comer são aleatórios, então nenhum filósofo fica com prioridade sobre os outros.

---

## Parte 2 — Threads e Semáforos

O objetivo era mostrar uma race condition incrementando um contador compartilhado sem sincronização, e depois corrigir com semáforo.

O GIL do CPython normalmente protege operações simples com threads, o que mascara a race condition. Pra conseguir mostrar a corrida com T=8 e M=200.000 usando threading, usamos um `bytearray` com leitura e escrita via `struct` — operações que o GIL não torna atômicas, então a intercalação entre threads aparece de verdade.

### Pseudocódigo

```
count = bytearray(8)
sem = Semaforo(1)

funcao tarefa():
    para i de 1 ate M:
        // versao sem sync (race condition):
        escrever(count, ler(count) + 1)

        // versao com semaforo (correta):
        sem.adquirir()
        try:
            escrever(count, ler(count) + 1)
        finally:
            sem.liberar()

programa principal:
    lançar T threads executando tarefa()
    esperar todas terminarem
    imprimir esperado = T*M, obtido = count
```

### Tabela de resultados

Configuração: T=8 threads, M=200.000 incrementos/thread, esperado=1.600.000

| Versão | Exec | Esperado | Obtido | Perdidos | Tempo (s) |
|---|---|---|---|---|---|
| Sem sync | #1 | 1.600.000 | 998.814 | 601.186 | 0,4492 |
| Sem sync | #2 | 1.600.000 | 773.493 | 826.507 | 0,4391 |
| Sem sync | #3 | 1.600.000 | 908.221 | 691.779 | 0,4827 |
| Com semáforo | #1 | 1.600.000 | 1.600.000 | 0 | 2,7031 |
| Com semáforo | #2 | 1.600.000 | 1.600.000 | 0 | 2,4982 |
| Com semáforo | #3 | 1.600.000 | 1.600.000 | 0 | 2,5045 |

### Discussão

**Por que sem sync perde incrementos?** Entre o `ler()` e o `escrever()`, outra thread pode ler o mesmo valor e sobrescrever o resultado. As duas escritas acontecem mas só uma vale — a outra é perdida.

**Por que com semáforo é correto?** O semáforo garante que só uma thread por vez executa a seção crítica. O `release()` cria uma barreira de memória implícita em Python, então a thread seguinte sempre enxerga o valor atualizado (equivalente ao happens-before do Java).

**Trade-off:** a versão com semáforo é em média ~5-6x mais lenta porque cada incremento precisa de acquire + release, com possível troca de contexto entre threads.

**Fairness:** o `threading.Semaphore` do Python usa uma fila interna, então as threads acabam tendo acesso de forma razoavelmente justa.

---

## Parte 3 — Deadlock

Duas threads, dois locks (A e B):
- Thread 1 pega LOCK_A, dorme 50ms, tenta LOCK_B
- Thread 2 pega LOCK_B, dorme 50ms, tenta LOCK_A

O sleep garante que as duas pegam o primeiro lock antes de qualquer uma tentar o segundo, então o deadlock acontece sempre.

As 4 condições de Coffman:
1. exclusão mútua — locks binários
2. manter-e-esperar — T1 segura LOCK_A enquanto espera LOCK_B e vice-versa
3. sem preempção — nenhuma libera o lock voluntariamente
4. espera circular — T1 espera T2, T2 espera T1

### Log do travamento

```
[T1] adquirindo LOCK_A...
[T2] adquirindo LOCK_B...
[T1] adquiriu LOCK_A. Dormindo 50ms...
[T2] adquiriu LOCK_B. Dormindo 50ms...
[T1] tentando LOCK_B... (vai travar se T2 ja pegou)
[T2] tentando LOCK_A... (vai travar se T1 ja pegou)

*** DEADLOCK CONFIRMADO: programa travado ***

=== DIAGNOSTICO DE THREADS (threading.enumerate) ===
  thread: MainThread | alive: True | daemon: False
  thread: Thread-1   | alive: True | daemon: True
  thread: Thread-2   | alive: True | daemon: True
```

### Correção

A correção foi impor que as duas threads sempre adquirem os locks na mesma ordem: LOCK_A antes de LOCK_B. Isso quebra a condição 4 de Coffman (espera circular) — se toda thread precisa de LOCK_A antes de LOCK_B, nunca vai ter T1 com A esperando B e T2 com B esperando A ao mesmo tempo.

```
// regra pra todas as threads:
adquirir(LOCK_A)
adquirir(LOCK_B)
// seção crítica
liberar(LOCK_B)
liberar(LOCK_A)
```

---

## Referências

- https://en.wikipedia.org/wiki/Dining_philosophers_problem
- https://en.wikipedia.org/wiki/Deadlock_(computer_science)
- https://docs.python.org/3/library/threading.html
- Silberschatz - Operating System Concepts cap. 8
