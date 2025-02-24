from util.http_stream_util import stream_events

if __name__ == "__main__":
    url = "http://localhost:8080/service/model/chat"
    payload = {
        "model_factory": "deepseek",
        "model_payload": {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "user",
                    "content": "你觉得人工智能什么时候可以达到AGI，请你具体分析"
                }
            ]
        },
        "stream": True,
    }


    def on_receive(data):
        print('receive: ', data)


    stream_events(url, payload, on_receive)
