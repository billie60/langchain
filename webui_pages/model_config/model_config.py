import importlib

import streamlit as st

from configs import prompt_config
from webui_pages.utils import *

def model_config_page(api: ApiRequest):
    pass

def prompt_config_page(api: ApiRequest, is_lite: bool = False):
    importlib.reload(prompt_config)
    new = st.button("新建提示词模板")
    if new:
        st.text_input("自定义模板")
    for prompt_name in prompt_config.PROMPT_TEMPLATES.keys():
        st.header(prompt_name)
        for prompt_type, prompt in prompt_config.PROMPT_TEMPLATES[prompt_name].items():
            st.text_area(prompt_type, prompt)