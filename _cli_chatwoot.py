"""
CLI de teste que simula um cliente mandando mensagem via Chatwoot.

Configure no .env do projeto:
  CHATWOOT_BASE_URL, CHATWOOT_API_TOKEN, CHATWOOT_ACCOUNT_ID, CHATWOOT_INBOX_ID
  TESTE_TELEFONE (opcional), TESTE_NOME (opcional)
"""

import os, sys, time
import httpx
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"), override=True)

BASE_URL   = os.getenv("CHATWOOT_BASE_URL", "").rstrip("/")
TOKEN      = os.getenv("CHATWOOT_API_TOKEN", "")
ACCOUNT_ID = os.getenv("CHATWOOT_ACCOUNT_ID", "1")
INBOX_ID   = int(os.getenv("CHATWOOT_INBOX_ID", "0"))
TELEFONE   = os.getenv("TESTE_TELEFONE", "5521900000099")
NOME       = os.getenv("TESTE_NOME", "Teste CLI")

POLL_INTERVALO = 2
POLL_TIMEOUT   = 45

def _headers():
    return {"api_access_token": TOKEN, "Content-Type": "application/json"}

def _api(path):
    return f"{BASE_URL}/api/v1/accounts/{ACCOUNT_ID}{path}"

def checar_config():
    erros = []
    if not BASE_URL: erros.append("CHATWOOT_BASE_URL nao definida")
    if not TOKEN:    erros.append("CHATWOOT_API_TOKEN nao definido")
    if not INBOX_ID: erros.append("CHATWOOT_INBOX_ID nao definido (ex: CHATWOOT_INBOX_ID=4)")
    if erros:
        print("\nConfiguracao incompleta no .env:")
        for e in erros:
            print(f"  - {e}")
        input("\nPressione Enter para fechar...")
        sys.exit(1)

def criar_ou_buscar_contato(client):
    r = client.get(_api("/contacts/search"), params={"q": TELEFONE}, headers=_headers())
    if r.status_code == 200:
        payload = r.json().get("payload", {})
        lista = payload if isinstance(payload, list) else payload.get("contacts", [])
        for c in lista:
            if TELEFONE in (c.get("phone_number") or ""):
                return c
            if TELEFONE in (c.get("identifier") or "").split("@")[0]:
                return c
    r = client.post(_api("/contacts"), json={
        "name": NOME,
        "phone_number": f"+{TELEFONE}",
        "identifier": f"{TELEFONE}@s.whatsapp.net",
    }, headers=_headers())
    r.raise_for_status()
    data = r.json()
    return data.get("contact", data)

def criar_conversa(client, contact_id):
    r = client.post(_api("/conversations"), json={
        "inbox_id": INBOX_ID,
        "contact_id": contact_id,
        "status": "open",
    }, headers=_headers())
    r.raise_for_status()
    return r.json()["id"]

def enviar_mensagem(client, conv_id, texto):
    r = client.post(_api(f"/conversations/{conv_id}/messages"), json={
        "content": texto,
        "message_type": 0,
        "private": False,
    }, headers=_headers())
    r.raise_for_status()
    return r.json()["id"]

def aguardar_resposta(client, conv_id, ultimo_id):
    inicio = time.time()
    ids_vistos = {ultimo_id}
    respostas = []
    print("   aguardando agente", end="", flush=True)
    while time.time() - inicio < POLL_TIMEOUT:
        time.sleep(POLL_INTERVALO)
        print(".", end="", flush=True)
        try:
            r = client.get(_api(f"/conversations/{conv_id}/messages"), headers=_headers())
            if r.status_code != 200:
                continue
            msgs = r.json().get("payload", [])
            novas = [m for m in msgs
                     if m["id"] not in ids_vistos
                     and m.get("message_type") in (1, "outgoing")
                     and not m.get("private", False)]
            if novas:
                print()
                for m in sorted(novas, key=lambda x: x["id"]):
                    t = m.get("content") or ""
                    if t:
                        respostas.append(t)
                        ids_vistos.add(m["id"])
                time.sleep(POLL_INTERVALO)
                return respostas
        except Exception as e:
            print(f"\n   erro polling: {e}")
    print()
    if not respostas:
        print("   timeout — veja no Chatwoot diretamente")
    return respostas

def main():
    checar_config()
    print("=" * 60)
    print("  AGENTE 2W PNEUS - Simulador Chatwoot")
    print(f"  Servidor : {BASE_URL}")
    print(f"  Inbox    : {INBOX_ID}")
    print(f"  Telefone : +{TELEFONE}")
    print("  Comandos : 'sair' | 'nova' (abre nova conversa)")
    print("=" * 60)

    with httpx.Client(timeout=15.0) as client:
        print("\nBuscando contato de teste...")
        try:
            contato = criar_ou_buscar_contato(client)
        except Exception as e:
            print(f"  ERRO ao criar contato: {e}")
            input("\nPressione Enter para fechar...")
            sys.exit(1)

        contact_id = contato["id"]
        print(f"  Contato #{contact_id} - {contato.get('name', NOME)}")

        print("Criando conversa...")
        try:
            conv_id = criar_conversa(client, contact_id)
        except Exception as e:
            print(f"  ERRO ao criar conversa: {e}")
            input("\nPressione Enter para fechar...")
            sys.exit(1)

        print(f"  Conversa #{conv_id} aberta no Chatwoot")
        print(f"\n  >> Abra o Chatwoot e procure a conversa #{conv_id} <<\n")

        ultimo_id = 0
        while True:
            try:
                msg = input("Voce: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nEncerrando.")
                break
            if not msg:
                continue
            if msg.lower() in ("sair", "exit"):
                print("Encerrando.")
                break
            if msg.lower() == "nova":
                conv_id = criar_conversa(client, contact_id)
                print(f"  Nova conversa #{conv_id}\n")
                ultimo_id = 0
                continue
            try:
                ultimo_id = enviar_mensagem(client, conv_id, msg)
            except Exception as e:
                print(f"  ERRO ao enviar: {e}")
                continue
            for resp in aguardar_resposta(client, conv_id, ultimo_id):
                print(f"\nAgente: {resp}")
            print()

if __name__ == "__main__":
    main()
