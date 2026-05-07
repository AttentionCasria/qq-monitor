import asyncio
import json
import websockets
import os

# 读取配置文件
def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'settings.json')
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件 {config_path} 未找到，请根据模板创建。")
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

config = load_config()

# ===== 你的配置 =====
BOT_QQ = config.get("BOT_QQ", 0)                  # 机器人小号
ADMIN_QQ = config.get("ADMIN_QQ", 0)              # 你的主号，接收通知
TARGET_GROUPS = config.get("TARGET_GROUPS", [])   # 需要监控的群号列表
KEYWORDS = config.get("KEYWORDS", [])             # 触发通知的关键词
WS_URL = config.get("WS_URL", "ws://127.0.0.1:8080")  # go-cqhttp 正向 WebSocket 地址
# ===================

async def listen():
    async with websockets.connect(WS_URL) as ws:
        print(f"已连接到 go-cqhttp，开始监控群消息...")
        while True:
            raw = await ws.recv()
            data = json.loads(raw)

            # 只处理群消息事件
            if data.get("post_type") == "message" and data.get("message_type") == "group":
                group_id = data.get("group_id")
                if group_id not in TARGET_GROUPS:
                    continue

                raw_msg = data.get("raw_message", "")
                # 检查是否包含任一关键词
                for word in KEYWORDS:
                    if word in raw_msg:
                        sender = data.get("sender", {}).get("nickname", "未知")
                        notify_text = (
                            f"【关键词触发通知】\n"
                            f"群号：{group_id}\n"
                            f"发言人：{sender}\n"
                            f"触发词：{word}\n"
                            f"消息内容：{raw_msg}"
                        )
                        # 发送私聊给管理员大号
                        send_data = {
                            "action": "send_private_msg",
                            "params": {
                                "user_id": ADMIN_QQ,
                                "message": notify_text
                            }
                        }
                        await ws.send(json.dumps(send_data))
                        print(f"已通知：群{group_id} {sender} 触发了「{word}」")
                        break  # 一条消息只通知一次

if __name__ == "__main__":
    try:
        asyncio.run(listen())
    except KeyboardInterrupt:
        print("监控已停止")
