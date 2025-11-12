"""
使用 OpenAI Python SDK 调用 LLM One API 的示例
"""

import openai


client = openai.OpenAI(base_url="http://localhost:8000/v1", api_key="sk-dev-test-key")


def chat_completion_example():
    """聊天补全示例"""
    print("=== 聊天补全示例 ===")
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "你是一个有帮助的助手。"},
            {"role": "user", "content": "请介绍一下 Python 编程语言。"}
        ],
        temperature=0.7,
    )
    
    print(f"回复: {response.choices[0].message.content}")
    print(f"Token 使用: {response.usage}")


def stream_example():
    """流式响应示例"""
    print("\n=== 流式响应示例 ===")
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": "写一首关于春天的短诗"}
        ],
        stream=True,
    )
    
    print("回复: ", end="", flush=True)
    for chunk in response:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
    print()


def embedding_example():
    """文本嵌入示例"""
    print("\n=== 文本嵌入示例 ===")
    
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input="这是一段需要嵌入的文本"
    )
    
    embedding = response.data[0].embedding
    print(f"嵌入向量维度: {len(embedding)}")
    print(f"前 5 个值: {embedding[:5]}")


def list_models_example():
    """列出模型示例"""
    print("\n=== 列出模型示例 ===")
    
    models = client.models.list()
    
    print("可用模型:")
    for model in models.data:
        print(f"  - {model.id}")


def multimodal_example():
    """多模态示例（文本 + 图片）"""
    print("\n=== 多模态示例 ===")
    import base64
    
    base64_image = base64.b64encode(open("demo.jpeg", "rb").read()).decode("utf-8")
    image_url = f"data:image/jpeg;base64,{base64_image}"
    image_url = "https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen-VL/assets/demo.jpeg"
    
    response = client.chat.completions.create(
        model="claude-sonnet-4.5",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "描述这个图片"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url
                        }
                    }
                ]
            }
        ],
    )
    
    print(f"回复: {response.choices[0].message.content}")


if __name__ == "__main__":
    try:
        chat_completion_example()
        # stream_example()
        
        # 如果模型支持多模态，取消注释下面这行
        # multimodal_example()
        
        # embedding_example()  # 需要配置 embedding 模型
        # list_models_example()
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

