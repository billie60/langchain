# encoding: utf-8
import base64
import hashlib
import hmac
import json
import random
import string
import sys
import time
import urllib.parse
import uuid
from typing import List, Dict

import requests
from fastchat import conversation as conv
from fastchat.conversation import Conversation

from server.model_workers import ApiModelWorker, ApiChatParams


# 随机字符串
def gen_nonce(length=8):
    chars = string.ascii_lowercase + string.digits
    return "".join([random.choice(chars) for _ in range(length)])


# 如果query项只有key没有value时，转换成params[key] = ''传入
def gen_canonical_query_string(params):
    if params:
        escape_uri = urllib.parse.quote
        raw = []
        for k in sorted(params.keys()):
            tmp_tuple = (escape_uri(k), escape_uri(str(params[k])))
            raw.append(tmp_tuple)
        s = "&".join("=".join(kv) for kv in raw)
        return s
    else:
        return ""


def gen_signature(app_secret, signing_string):
    bytes_secret = app_secret.encode("utf-8")
    hash_obj = hmac.new(bytes_secret, signing_string, hashlib.sha256)
    bytes_sig = base64.b64encode(hash_obj.digest())
    signature = str(bytes_sig, encoding="utf-8")
    return signature


def gen_sign_headers(app_id, app_key, method, uri, query):
    method = str(method).upper()
    uri = uri
    timestamp = str(int(time.time()))
    app_id = app_id
    app_key = app_key
    nonce = gen_nonce()
    canonical_query_string = gen_canonical_query_string(query)
    signed_headers_string = (
        "x-ai-gateway-app-id:{}\nx-ai-gateway-timestamp:{}\n"
        "x-ai-gateway-nonce:{}".format(app_id, timestamp, nonce)
    )
    signing_string = "{}\n{}\n{}\n{}\n{}\n{}".format(
        method, uri, canonical_query_string, app_id, timestamp, signed_headers_string
    )
    signing_string = signing_string.encode("utf-8")
    signature = gen_signature(app_key, signing_string)
    return {
        "X-AI-GATEWAY-APP-ID": app_id,
        "X-AI-GATEWAY-TIMESTAMP": timestamp,
        "X-AI-GATEWAY-NONCE": nonce,
        "X-AI-GATEWAY-SIGNED-HEADERS": "x-ai-gateway-app-id;x-ai-gateway-timestamp;x-ai-gateway-nonce",
        "X-AI-GATEWAY-SIGNATURE": signature,
    }


class VivoWorker(ApiModelWorker):
    def __init__(
        self,
        *,
        model_names: List[str] = ["vivo-api"],
        controller_addr: str = None,
        worker_addr: str = None,
        **kwargs,
    ):
        kwargs.update(
            model_names=model_names,
            controller_addr=controller_addr,
            worker_addr=worker_addr,
        )
        kwargs.setdefault("context_len", 8000)
        super().__init__(**kwargs)

    def do_chat(self, params: ApiChatParams) -> Dict:
        params.load_config(self.model_names[0])
        URI = "/vivogpt/completions/stream"
        DOMAIN = "api-ai.vivo.com.cn"
        METHOD = "POST"
        vivo_params = {"requestId": str(uuid.uuid4())}
        data = {
            "messages": params.messages,
            "sessionId": str(uuid.uuid4()),
            "model": "vivo-BlueLM-TB",
        }
        headers = gen_sign_headers(
            params.app_id, params.app_key, METHOD, URI, vivo_params
        )
        headers["Content-Type"] = "application/json"

        url = "http://{}{}".format(DOMAIN, URI)
        response = requests.post(
            url, json=data, headers=headers, params=vivo_params, stream=True
        )
        text = ""
        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    line_str = line.decode("utf-8", errors="ignore")
                    if line_str.startswith("data:{"):
                        line_data = line_str[5:]
                        resp = json.loads(line_data)
                        if "reply" in resp:
                            text += resp["reply"]
                            yield {"error_code": 0, "text": text}
                        elif "msg" in resp:
                            yield {
                                "error_code": resp["code"],
                                "text": resp["msg"],
                                "error": {
                                    "message": resp["msg"],
                                    "type": "invalid_request_error",
                                    "param": None,
                                    "code": None,
                                },
                            }
                        else:
                            text += resp["message"]
                            yield {"error_code": 0, "text": text}
        else:
            err = {
                "error_code": response.status_code,
                "text": response.text,
                "error": {
                    "message": response.text,
                    "type": "invalid_request_error",
                    "param": None,
                    "code": None,
                },
            }
            self.logger.error(f"请求vivo API 时发生错误：{err}")
            yield err

    def get_embeddings(self, params):
        # Implement embedding retrieval if necessary
        print("embedding")
        print(params)

    def make_conv_template(
        self, conv_template: str = None, model_path: str = None
    ) -> Conversation:
        return conv.Conversation(
            name=self.model_names[0],
            system_message="你是一个聪明、对人类有帮助的人工智能，你可以对人类提出的问题给出有用、详细、礼貌的回答。",
            messages=[],
            roles=["user", "assistant", "system"],
            sep="\n### ",
            stop_str="###",
        )


if __name__ == "__main__":
    import uvicorn
    from server.utils import MakeFastAPIOffline
    from fastchat.serve.model_worker import app

    worker = VivoWorker(
        controller_addr="http://127.0.0.1:20001",
        worker_addr="http://127.0.0.1:21011",
    )
    sys.modules["fastchat.serve.model_worker"].worker = worker
    MakeFastAPIOffline(app)
    uvicorn.run(app, port=21011)
