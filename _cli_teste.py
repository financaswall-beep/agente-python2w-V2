"""CLI interativo para testar o agente localmente."""
import sys
from uuid import UUID
from agente_2w.engine.orquestrador._nucleo import processar_turno

SESSAO_ID = UUID("6e7f5e96-6e54-4af6-8ee1-fca77e55daca")

print("=" * 60)
print("AGENTE 2W PNEUS — teste interativo")
print(f"sessao: {SESSAO_ID}")
print("Digite sua mensagem. 'sair' para encerrar.")
print("=" * 60)

while True:
    try:
        msg = input("\nVocê: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nEncerrando.")
        break
    if msg.lower() in ("sair", "exit", "quit"):
        break
    if not msg:
        continue
    resposta = processar_turno(SESSAO_ID, msg)
    print(f"\nAgente: {resposta.texto}")
