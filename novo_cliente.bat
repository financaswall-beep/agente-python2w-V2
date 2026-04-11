@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

set BASE_URL=http://rails-i11zge2c4lemo09tzmnf4ggx.76.13.164.152.sslip.io
set TOKEN=jtA9abmpgCbLxGE4mMZKBaY9
set ACCOUNT_ID=1
set INBOX_ID=3
set CONV_ID=
set DEBUG=1

:menu
echo.
echo ============================================
echo   2W PNEUS - CHAT COM O AGENTE
echo ============================================
echo  1. Novo cliente (numero aleatorio)
echo  2. Conversa existente (informar ID)
echo  3. Listar conversas abertas
echo  4. Toggle debug (atual: %DEBUG%)
echo  0. Sair
echo ============================================
set /p opcao="Opcao: "

if "%opcao%"=="1" goto novo_cliente
if "%opcao%"=="2" goto conversa_existente
if "%opcao%"=="3" goto listar
if "%opcao%"=="4" goto toggle_debug
if "%opcao%"=="0" goto sair
echo Opcao invalida.
goto menu

:toggle_debug
if "%DEBUG%"=="1" (set DEBUG=0) else (set DEBUG=1)
echo Debug agora: %DEBUG%
goto menu

:listar
echo.
echo --- Conversas abertas ---
curl -s -H "api_access_token: %TOKEN%" "%BASE_URL%/api/v1/accounts/%ACCOUNT_ID%/conversations?status=open&page=1" > %TEMP%\cw_resp.json
python -c "import json;d=json.load(open(r'%TEMP%\cw_resp.json'));convs=d.get('data',{}).get('payload',[]);print(f'Total: {len(convs)}');[print(f'  ID:{c[\"id\"]:>4} | {c.get(\"meta\",{}).get(\"sender\",{}).get(\"name\",\"?\")} | labels:{c.get(\"labels\",[])}') for c in convs[:15]]"
echo.
pause
goto menu

:novo_cliente
echo.
set /p nome="Nome do cliente: "
for /f %%i in ('python -c "import random;print(f'5521{random.randint(900000000,999999999)}')"') do set telefone=%%i
echo [+] Telefone gerado: +%telefone%

:: Criar contato
echo {"name":"%nome%","phone_number":"+%telefone%"} > %TEMP%\cw_body.json
curl -s -X POST -H "api_access_token: %TOKEN%" -H "Content-Type: application/json" -d @%TEMP%\cw_body.json "%BASE_URL%/api/v1/accounts/%ACCOUNT_ID%/contacts" > %TEMP%\cw_resp.json
if "%DEBUG%"=="1" (
    echo [DEBUG] Resposta criar contato:
    python -c "import json;print(json.dumps(json.load(open(r'%TEMP%\cw_resp.json')),indent=2,ensure_ascii=False))"
)
for /f %%i in ('python -c "import json;d=json.load(open(r'%TEMP%\cw_resp.json'));print(d.get('payload',{}).get('contact',{}).get('id',d.get('id','erro')))"') do set CONTACT_ID=%%i
echo [+] Contato criado: ID=%CONTACT_ID%

:: Vincular contato ao inbox
echo {"inbox_id":%INBOX_ID%} > %TEMP%\cw_body.json
curl -s -X POST -H "api_access_token: %TOKEN%" -H "Content-Type: application/json" -d @%TEMP%\cw_body.json "%BASE_URL%/api/v1/accounts/%ACCOUNT_ID%/contacts/%CONTACT_ID%/contact_inboxes" > %TEMP%\cw_resp.json
if "%DEBUG%"=="1" (
    echo [DEBUG] Resposta contact_inbox:
    python -c "import json;print(json.dumps(json.load(open(r'%TEMP%\cw_resp.json')),indent=2,ensure_ascii=False))"
)
for /f %%i in ('python -c "import json;d=json.load(open(r'%TEMP%\cw_resp.json'));print(d.get('source_id',d.get('payload',{}).get('source_id','?')))"') do set SOURCE_ID=%%i
echo [+] Contact inbox vinculado (source: %SOURCE_ID%)

:: Criar conversa
echo {"inbox_id":%INBOX_ID%,"contact_id":%CONTACT_ID%,"source_id":"%SOURCE_ID%"} > %TEMP%\cw_body.json
curl -s -X POST -H "api_access_token: %TOKEN%" -H "Content-Type: application/json" -d @%TEMP%\cw_body.json "%BASE_URL%/api/v1/accounts/%ACCOUNT_ID%/conversations" > %TEMP%\cw_resp.json
if "%DEBUG%"=="1" (
    echo [DEBUG] Resposta criar conversa:
    python -c "import json;print(json.dumps(json.load(open(r'%TEMP%\cw_resp.json')),indent=2,ensure_ascii=False))"
)
for /f %%i in ('python -c "import json;print(json.load(open(r'%TEMP%\cw_resp.json')).get('id','erro'))"') do set CONV_ID=%%i
echo [+] Conversa criada: ID=%CONV_ID%
echo 0> %TEMP%\cw_last_check.txt
goto chat

:conversa_existente
echo.
set /p CONV_ID="ID da conversa: "
echo 0> %TEMP%\cw_last_check.txt
:: Pegar ultima msg pra nao repetir historico
curl -s -H "api_access_token: %TOKEN%" "%BASE_URL%/api/v1/accounts/%ACCOUNT_ID%/conversations/%CONV_ID%/messages" > %TEMP%\cw_msgs.json
python -c "import json;msgs=json.load(open(r'%TEMP%\cw_msgs.json')).get('payload',[]);out=[m for m in msgs if m.get('message_type')==1 and not m.get('private')];f=open(r'%TEMP%\cw_last_check.txt','w');f.write(str(out[0]['id']) if out else '0');f.close()" 2>nul
echo [+] Conectado na conversa %CONV_ID%
goto chat

:chat
echo.
echo ============================================
echo   CHAT - Conversa %CONV_ID%
echo   Digite mensagem e ENTER para enviar
echo   Comandos: /menu  /labels  /info  /sair
echo ============================================

:chat_loop
echo.
set "msg="
set /p msg="Voce: "
if /i "%msg%"=="/sair" goto menu
if /i "%msg%"=="/menu" goto menu
if /i "%msg%"=="/labels" goto ver_labels
if /i "%msg%"=="/info" goto ver_info
if "%msg%"=="" goto chat_loop

:: Enviar como incoming
if "%DEBUG%"=="1" echo [DEBUG] Enviando msg incoming na conv %CONV_ID%...
echo {"content":"%msg%","message_type":"incoming"} > %TEMP%\cw_body.json
curl -s -X POST -H "api_access_token: %TOKEN%" -H "Content-Type: application/json" -d @%TEMP%\cw_body.json "%BASE_URL%/api/v1/accounts/%ACCOUNT_ID%/conversations/%CONV_ID%/messages" > %TEMP%\cw_send.json
if "%DEBUG%"=="1" (
    echo [DEBUG] Resposta envio:
    python -c "import json;d=json.load(open(r'%TEMP%\cw_send.json'));print(f'  msg_id={d.get(\"id\",\"?\")} status={d.get(\"status\",\"?\")}')" 2>nul
)

:: Aguardar resposta do agente
echo Aguardando agente...
set tentativas=0
:espera
if !tentativas! GEQ 20 (
    echo [!] Timeout 40s sem resposta. Tente /info ou veja no Chatwoot.
    goto chat_loop
)
timeout /t 2 /nobreak > nul
set /a tentativas+=1
if "%DEBUG%"=="1" (
    set /a segs=tentativas*2
    <nul set /p "=  [!segs!s] "
)

:: Buscar mensagens
curl -s -H "api_access_token: %TOKEN%" "%BASE_URL%/api/v1/accounts/%ACCOUNT_ID%/conversations/%CONV_ID%/messages" > %TEMP%\cw_msgs.json
python -c "import json;msgs=json.load(open(r'%TEMP%\cw_msgs.json')).get('payload',[]);out=[m for m in msgs if m.get('message_type')==1 and not m.get('private')];last=out[0] if out else None;f=open(r'%TEMP%\cw_last_id.txt','w');f.write(str(last['id']) if last else '0');f.close();f2=open(r'%TEMP%\cw_last_msg.txt','w',encoding='utf-8');f2.write(last.get('content','') if last else '');f2.close()" 2>nul

set /p LAST_CHECK=<%TEMP%\cw_last_check.txt
set /p NEW_ID=<%TEMP%\cw_last_id.txt

if "%NEW_ID%"=="0" goto espera
if "%NEW_ID%"=="%LAST_CHECK%" goto espera

:: Nova resposta!
echo %NEW_ID%> %TEMP%\cw_last_check.txt
if "%DEBUG%"=="1" echo [DEBUG] msg_id=%NEW_ID%
echo.
echo ------------------------------------------
echo Agente:
python -c "print(open(r'%TEMP%\cw_last_msg.txt',encoding='utf-8').read())"
echo ------------------------------------------
goto chat_loop

:ver_labels
echo.
curl -s -H "api_access_token: %TOKEN%" "%BASE_URL%/api/v1/accounts/%ACCOUNT_ID%/conversations/%CONV_ID%/labels" > %TEMP%\cw_resp.json
echo Labels da conversa %CONV_ID%:
python -c "import json;d=json.load(open(r'%TEMP%\cw_resp.json'));print('  ',d.get('payload',[]))"
goto chat_loop

:ver_info
echo.
curl -s -H "api_access_token: %TOKEN%" "%BASE_URL%/api/v1/accounts/%ACCOUNT_ID%/conversations/%CONV_ID%" > %TEMP%\cw_resp.json
python -c "import json;c=json.load(open(r'%TEMP%\cw_resp.json'));s=c.get('meta',{}).get('sender',{});print(f'  Conversa: {c.get(\"id\")}');print(f'  Status: {c.get(\"status\")}');print(f'  Contato: {s.get(\"name\",\"?\")} (id:{s.get(\"id\",\"?\")})');print(f'  Labels: {c.get(\"labels\",[])}');ca=c.get('custom_attributes',{});print(f'  Custom: {ca}' if ca else '  Custom: (vazio)')"
goto chat_loop

:sair
del %TEMP%\cw_last_check.txt 2>nul
echo Ate mais!
endlocal
exit /b 0
