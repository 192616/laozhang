"""
机械百科助手 - Coze API 后端服务
运行前请先安装依赖：pip install flask requests
启动方式：python server.py
"""

from flask import Flask, request, jsonify, send_file
import requests
import time

app = Flask(__name__)

# Coze API 配置（使用 v3 接口）
COZE_API_URL = "https://api.coze.cn/v3/chat"
BOT_ID = "7632158079916294182"
PAT_TOKEN = "pat_lUkJRaGVUBgI2nYlxXBLew8Yj7GMvVdCr19IJCQfaLJYhmnVwOaoa2CVBvxWvMtZ"

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': '消息不能为空'}), 400
        
        print("[调试] 收到消息: " + user_message)
        
        headers = {
            "Authorization": "Bearer " + PAT_TOKEN,
            "Content-Type": "application/json"
        }
        
        payload = {
            "bot_id": BOT_ID,
            "user_id": "course_project_user",
            "stream": False,
            "auto_save_history": True,
            "additional_messages": [
                {
                    "role": "user",
                    "content": user_message,
                    "content_type": "text"
                }
            ]
        }
        
        print("[调试] 发送请求到 Coze API...")
        response = requests.post(COZE_API_URL, headers=headers, json=payload, timeout=60)
        result = response.json()
        print("[调试] API响应: " + str(result))
        
        if result.get('code') == 0:
            chat_id = result['data']['id']
            conversation_id = result['data']['conversation_id']
            print("[调试] chat_id: " + chat_id + ", conversation_id: " + conversation_id)
            return get_chat_result(headers, chat_id, conversation_id)
        else:
            print("[调试] API错误: " + str(result.get('msg', '未知错误')))
            return jsonify({'error': "Coze API 错误: " + str(result.get('msg', '未知错误'))}), 500
            
    except Exception as e:
        print("[调试] 异常: " + str(e))
        return jsonify({'error': str(e)}), 500

def get_chat_result(headers, chat_id, conversation_id, max_retries=60):
    retrieve_url = "https://api.coze.cn/v3/chat/retrieve?chat_id=" + chat_id + "&conversation_id=" + conversation_id
    
    print("[调试] 开始轮询获取结果...")
    
    for i in range(max_retries):
        try:
            response = requests.get(retrieve_url, headers=headers, timeout=30)
            result = response.json()
            print("[调试] 轮询第" + str(i+1) + "次，响应: " + str(result))
            
            if result.get('code') == 0:
                status = result['data']['status']
                print("[调试] 状态: " + status)
                
                if status == 'completed':
                    messages_url = "https://api.coze.cn/v3/chat/message/list?chat_id=" + chat_id + "&conversation_id=" + conversation_id
                    print("[调试] 获取消息列表...")
                    msg_response = requests.get(messages_url, headers=headers, timeout=30)
                    msg_result = msg_response.json()
                    print("[调试] 消息响应: " + str(msg_result))
                    
                    if msg_result.get('code') == 0:
                        messages = msg_result['data']
                        print("[调试] 消息数量: " + str(len(messages) if messages else 0))
                        
                        for msg in messages:
                            print("[调试] 消息类型: " + str(msg.get('type')) + ", role: " + str(msg.get('role')))
                            if msg.get('type') == 'answer' and msg.get('role') == 'assistant':
                                content = msg.get('content', '')
                                print("[调试] 找到回复: " + content[:100] + "...")
                                return jsonify({'response': content})
                        
                        return jsonify({'response': '抱歉，助手没有回复'})
                    
                    return jsonify({'response': '获取消息列表失败'})
                    
            elif result.get('code') == 1001:
                print("[调试] Token无效")
                return jsonify({'error': 'Token无效，请检查PAT配置'}), 500
                    
        except Exception as e:
            print("[调试] 轮询异常: " + str(e))
        
        time.sleep(2)
    
    print("[调试] 等待超时")
    return jsonify({'error': '等待超时，请重试'}), 500

if __name__ == '__main__':
    print("=" * 50)
    print("  机械百科助手 - 启动中...")
    print("  请在浏览器打开: http://127.0.0.1:5000")
    print("  按 Ctrl+C 停止服务")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)
