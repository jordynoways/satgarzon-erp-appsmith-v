import os.path
import base64
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.modify'] # Cambiado a modify para poder marcar como leído
DESTINO = '/home/garzon/garzon-pedidos/nuevos_washtec'
# Solo correos NO LEÍDOS en esa etiqueta
QUERY = 'label:"pedidos ISTOBAL/WASHTEC" is:unread'

def main():
    if not os.path.exists(DESTINO):
        os.makedirs(DESTINO)
    
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    service = build('gmail', 'v1', credentials=creds)
    
    print(f"Buscando pedidos NUEVOS (no leídos) en WashTec...")
    results = service.users().messages().list(userId='me', q=QUERY).execute()
    messages = results.get('messages', [])

    if not messages:
        print("📭 No hay pedidos nuevos por procesar.")
    else:
        print(f"📩 ¡Encontrados {len(messages)} pedidos nuevos! Descargando...")
        for message in messages:
            msg_id = message['id']
            msg = service.users().messages().get(userId='me', id=msg_id).execute()
            payload = msg.get('payload', {})
            parts = payload.get('parts', [])
            
            pdf_descargado = False
            for part in parts:
                if part['filename'] and part['filename'].lower().endswith('.pdf'):
                    att_id = part['body'].get('attachmentId')
                    if att_id:
                        attachment = service.users().messages().attachments().get(
                            userId='me', messageId=msg_id, id=att_id).execute()
                        data = base64.urlsafe_b64decode(attachment['data'].encode('UTF-8'))
                        
                        filepath = os.path.join(DESTINO, part['filename'])
                        with open(filepath, 'wb') as f:
                            f.write(data)
                        print(f"✅ Guardado: {part['filename']}")
                        pdf_descargado = True
            
            # SI SE DESCARGÓ EL PDF, MARCAMOS COMO LEÍDO PARA QUE NO SE REPITA
            if pdf_descargado:
                service.users().messages().batchModify(
                    userId='me',
                    body={'ids': [msg_id], 'removeLabelIds': ['UNREAD']}
                ).execute()
                print(f"🏷️ Correo {msg_id} marcado como procesado.")

if __name__ == '__main__':
    main()
