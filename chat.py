from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import os
from dotenv import load_dotenv, find_dotenv
from openai import OpenAI

_ = load_dotenv(find_dotenv())

app = FastAPI()

# 确保您在环境变量中设置了 DeepSeek API 密钥
DEEPSEEK_API_KEY = os.getenv("OPENAI_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("OPENAI_BASE_URL")
MODEL = os.getenv("MODEL")
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

# 从文件中读取 prompt
with open('mall_guide_robot_prompt.txt', 'r', encoding='utf-8') as file:
    SYSTEM_PROMPT = file.read().strip()

# 前端页面的 HTML 模板
html_template = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>ChatGPT 聊天机器人</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #eef1f5;
            margin: 0;
            padding: 0;
        }
        #chat-container {
            width: 60%;
            max-width: 800px;
            margin: 50px auto;
            background-color: #fff;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        #messages {
            height: 500px;
            overflow-y: auto;
            border-bottom: 1px solid #ddd;
            padding-bottom: 15px;
            margin-bottom: 15px;
        }
        .message {
            margin: 10px 0;
            line-height: 1.6;
        }
        .user {
            text-align: right;
            color: #007BFF;
        }
        .assistant {
            text-align: left;
            color: #343A40;
        }
        #input-form {
            display: flex;
        }
        #user-input {
            flex: 1;
            padding: 12px;
            font-size: 16px;
            border: 1px solid #ced4da;
            border-radius: 4px;
            outline: none;
        }
        #input-form button {
            padding: 12px 20px;
            font-size: 16px;
            margin-left: 10px;
            background-color: #007BFF;
            border: none;
            color: #fff;
            border-radius: 4px;
            cursor: pointer;
        }
        #input-form button:hover {
            background-color: #0056b3;
        }
    </style>
</head>
<body>

<div id="chat-container">
    <div id="messages">
        <!-- 聊天记录将显示在这里 -->
    </div>
    <form id="input-form">
        <input type="text" id="user-input" placeholder="请输入您的消息..." autocomplete="off" required>
        <button type="submit">发送</button>
    </form>
</div>

<script>
    const messagesDiv = document.getElementById('messages');
    const inputForm = document.getElementById('input-form');
    const userInput = document.getElementById('user-input');

    let conversation = [];

    inputForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const userText = userInput.value.trim();
        if (userText === '') return;
        addMessage(userText, 'user');
        userInput.value = '';
        conversation.push({"role": "user", "content": userText});
        getResponse();
    });

    function addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', sender);
        messageDiv.innerText = text;
        messagesDiv.appendChild(messageDiv);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }

    async function getResponse() {
        addMessage('正在思考...', 'assistant');
        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    "messages": conversation
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP 错误！状态码：${response.status}`);
            }

            const data = await response.json();
            const assistantMessage = data.reply.trim();
            conversation.push({"role": "assistant", "content": assistantMessage});
            // 移除"正在思考..."占位符
            messagesDiv.removeChild(messagesDiv.lastChild);
            addMessage(assistantMessage, 'assistant');
        } catch (error) {
            console.error('错误：', error);
            messagesDiv.removeChild(messagesDiv.lastChild);
            addMessage('获取回复时出错。', 'assistant');
        }
    }
</script>

</body>
</html>
"""

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "html_template": html_template})

@app.post("/chat", response_class=JSONResponse)
async def chat(request: Request):
    data = await request.json()
    messages = data.get('messages', [])
    
    # 添加系统提示
    system_message = {
        "role": "system",
        "content": SYSTEM_PROMPT
    }
    messages.insert(0, system_message)
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            stream=False
        )
        assistant_message = response.choices[0].message.content
        return {"reply": assistant_message}
    except Exception as e:
        print(f'错误：{e}')
        raise HTTPException(status_code=500, detail=str(e))
