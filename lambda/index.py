import json
import os
import re
import urllib.request
from urllib.error import URLError, HTTPError

# FastAPI inference endpoint
API_URL = "https://ade6-34-32-198-21.ngrok-free.app/generate"

# モデルIDや Bedrock クライアントは不要となったため削除しました

def lambda_handler(event, context):
    try:
        # イベント受信ログ
        print("Received event:", json.dumps(event))
        
        # Cognito 認証情報の取得
        user_info = None
        if 'requestContext' in event and 'authorizer' in event['requestContext']:
            user_info = event['requestContext']['authorizer']['claims']
            print(f"Authenticated user: {user_info.get('email') or user_info.get('cognito:username')}")
        
        # リクエストボディの解析
        body = json.loads(event.get('body', '{}'))
        message = body.get('message', '')
        conversation_history = body.get('conversationHistory', [])
        
        print("Processing message:", message)
        
        # 外部 FastAPI への呼び出し
        payload = json.dumps({"prompt": message}).encode('utf-8')
        req = urllib.request.Request(
            API_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
            method='POST'
        )
        print("Calling external API with payload:", payload)
        
        with urllib.request.urlopen(req) as resp:
            resp_data = resp.read().decode('utf-8')
        print("External API response:", resp_data)
        
        # 外部 API のレスポンスを解析
        response_body = json.loads(resp_data)
        assistant_response = response_body.get('generated_text', '') or response_body.get('response', '') or response_body.get('content', '')
        
        # 会話履歴を更新
        messages = conversation_history.copy()
        messages.append({"role": "user", "content": message})
        messages.append({"role": "assistant", "content": assistant_response})
        
        # 成功レスポンスを返却
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": True,
                "response": assistant_response,
                "conversationHistory": messages
            })
        }
    except (HTTPError, URLError) as error:
        print("HTTP error calling external API:", error)
        return {
            "statusCode": 502,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"success": False, "error": str(error)})
        }
    except Exception as error:
        print("Error:", str(error))
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"success": False, "error": str(error)})
        }
