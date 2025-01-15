from openai import OpenAI
import gradio as gr
import os
from ppt_generator import generate_presentation
from input_parser import parse_input_text
from layout_manager import LayoutManager
from config import Config
from logger import LOG  # 引入 LOG 模块

# 初始化 OpenAI 客户端
client = OpenAI(
    api_key=os.environ.get("aihubmix_key"), base_url="https://api.aihubmix.com/v1"
)

# 读取 System Prompt
with open('prompts/formatter.txt', 'r') as file:
    FORMATTER_PROMPT = file.read()

GENERAL_PROMPT = "You are a helpful assistant capable of general conversations and answering questions."

# 定义对话历史
history = [{"role": "system", "content": GENERAL_PROMPT}]  # Chatbot 历史
formatter_history = [{"role": "system", "content": FORMATTER_PROMPT}]  # 格式化任务历史

# 调用 OpenAI API 的通用函数
def chat_with_openai(history, model="gpt-4o-mini"):
    try:
        LOG.info(f"Sending message to OpenAI: {history[-1]['content']}")  # 记录消息内容
        response = client.chat.completions.create(
            model=model,
            messages=history
        )
        LOG.info(f"Received response from OpenAI: {response.choices[0].message.content}")  # 记录返回内容
        return response.choices[0].message.content
    except Exception as e:
        LOG.error(f"Error during OpenAI API call: {str(e)}")
        return f"Error: {str(e)}"

# 定义从内容生成 PPTX 文件的函数
def generate_pptx(content):
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)  # 确保输出目录存在
    LOG.info(f"Starting PPTX generation with content: {content[:100]}...")  # 日志前100个字符，避免过长

    try:
        config = Config()  # 加载配置文件
        layout_manager = LayoutManager(config.layout_mapping)  # 初始化 LayoutManager
        powerpoint_data, presentation_title = parse_input_text(content, layout_manager)
        LOG.info(f"Parsed PowerPoint data for title: {presentation_title}")  # 记录解析后的标题

        # 定义输出 PowerPoint 文件的路径
        output_pptx = os.path.join(output_dir, f"{presentation_title}.pptx")
        # 调用生成 PPT 的函数
        generate_presentation(powerpoint_data, config.ppt_template, output_pptx)
        LOG.info(f"PPTX generated successfully: {output_pptx}")
        return output_pptx
    except Exception as e:
        LOG.error(f"Error generating PPTX: {str(e)}")
        return f"Error generating PPTX: {str(e)}"

# 定义 Gradio 应用
with gr.Blocks() as demo:
    chatbot = gr.Chatbot(label="Chatbot", type="messages")
    msg = gr.Textbox(label="Enter your message")
    clear = gr.Button("Clear")
    send_to_formatter = gr.Button("Send to Formatter")
    ppt_output = gr.Textbox(label="Generated PPT Content")
    generate_pptx_btn = gr.Button("Generate PPTX")
    pptx_file = gr.File(label="Download PPTX")

    def respond(message):
        global history
        LOG.info(f"User input: {message[:20]}")  # 记录用户输入
        history.append({"role": "user", "content": message})
        response = chat_with_openai(history)
        history.append({"role": "assistant", "content": response})
        return "", history

    def clear_history():
        global history, formatter_history
        LOG.info("Clearing history.")  # 记录历史清除
        history = [{"role": "system", "content": GENERAL_PROMPT}]
        formatter_history = [{"role": "system", "content": FORMATTER_PROMPT}]
        return []

    def send_to_formatter_func():
        global formatter_history
        LOG.info("Sending response to formatter.")  # 记录格式化任务
        last_content = next((item['content'] for item in reversed(history) if item['role'] == 'assistant'), None)
        formatter_history.append({"role": "user", "content": last_content})
        response = chat_with_openai(formatter_history)
        formatter_history.append({"role": "assistant", "content": response})
        return response

    def generate_pptx_file(ppt_content):
        if not ppt_content.strip():
            LOG.warning("PPT content is empty.")  # 记录内容为空警告
            return "Error: PPT content is empty."
        return generate_pptx(ppt_content)

    msg.submit(respond, [msg], [msg, chatbot])
    clear.click(clear_history, None, chatbot)
    send_to_formatter.click(send_to_formatter_func, None, ppt_output)
    generate_pptx_btn.click(generate_pptx_file, ppt_output, pptx_file)

# 启动 Gradio 应用
if __name__ == "__main__":
    LOG.info("Starting Gradio app.")  # 记录启动
    demo.launch(show_error=True, share=True)
