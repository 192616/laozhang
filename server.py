from flask import Flask, request, jsonify, send_file
import requests
import time
import re

app = Flask(__name__)

COZE_API_URL = "https://api.coze.cn/v3/chat"
BOT_ID = "7632158079916294182"
PAT_TOKEN = "pat_lUkJRaGVUBgI2nYlxXBLew8Yj7GMvVdCr19IJCQfaLJYhmnVwOaoa2CVBvxWvMtZ"

def preprocess_latex(text):
    text = text.replace("\\\\", "\\")
    text = re.sub(r"\\_", "_", text)
    
    greek_map = {
        "\\alpha": "α", "\\beta": "β", "\\gamma": "γ", "\\delta": "δ",
        "\\epsilon": "ε", "\\zeta": "ζ", "\\eta": "η", "\\theta": "θ",
        "\\iota": "ι", "\\kappa": "κ", "\\lambda": "λ", "\\mu": "μ",
        "\\nu": "ν", "\\xi": "ξ", "\\pi": "π", "\\rho": "ρ",
        "\\sigma": "σ", "\\tau": "τ", "\\upsilon": "υ", "\\phi": "φ",
        "\\chi": "χ", "\\psi": "ψ", "\\omega": "ω",
    }
    for greek, symbol in greek_map.items():
        text = text.replace(greek, symbol)
    
    special_map = {
        "\\times": "×", "\\div": "÷", "\\cdot": "·", "\\pm": "±",
        "\\geq": "≥", "\\leq": "≤", "\\neq": "≠", "\\approx": "≈",
        "\\infty": "∞", "\\partial": "∂", "\\nabla": "∇",
        "\\rightarrow": "→", "\\leftarrow": "←", "\\Rightarrow": "⇒",
    }
    for latex, symbol in special_map.items():
        text = text.replace(latex, symbol)
    
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\$\$\s*\n", "$$ ", text)
    text = re.sub(r"\n\s*\$\$", " $$", text)
    
    return text

@app.route("/")
def index():
    return send_file("index.html")

@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_message = data.get("message", "")
        
        if not user_message:
            return jsonify({"error": "消息不能为空"}), 400
        
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
        
        response = requests.post(COZE_API_URL, headers=headers, json=payload, timeout=30)
        result = response.json()
        
        if result.get("code") != 0:
            return jsonify({"error": "API错误: " + result.get("msg", "Unknown error")}), 500
        
        chat_data = result.get("data", {})
        chat_id = chat_data.get("id")
        conversation_id = chat_data.get("conversation_id")
        
        max_retries = 60
        for i in range(max_retries):
            time.sleep(1)
            
            retrieve_url = f"https://api.coze.cn/v3/chat/retrieve?chat_id={chat_id}&conversation_id={conversation_id}"
            retrieve_response = requests.get(retrieve_url, headers=headers, timeout=10)
            retrieve_result = retrieve_response.json()
            
            status = retrieve_result.get("data", {}).get("status")
            
            if status == "completed":
                messages_url = f"https://api.coze.cn/v3/chat/message/list?chat_id={chat_id}&conversation_id={conversation_id}"
                messages_response = requests.get(messages_url, headers=headers, timeout=10)
                messages_result = messages_response.json()
                
                messages = messages_result.get("data", [])
                for msg in messages:
                    if msg.get("role") == "assistant" and msg.get("type") == "answer":
                        answer = msg.get("content", "")
                        answer = preprocess_latex(answer)
                        return jsonify({"response": answer})
                
                return jsonify({"response": "抱歉，未能获取到回答"})
            
            elif status == "failed":
                return jsonify({"error": "AI处理失败，请稍后重试"}), 500
        
        return jsonify({"error": "等待超时，请稍后重试"}), 500
        
    except requests.exceptions.Timeout:
        return jsonify({"error": "请求超时，请稍后重试"}), 500
    except Exception as e:
        return jsonify({"error": "服务器错误: " + str(e)}), 500

if __name__ == "__main__":
    print("=" * 50)
    print("机械百科助手启动中...")
    print("请在浏览器打开: http://127.0.0.1:5000")
    print("按 Ctrl+C 停止服务")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=True)

