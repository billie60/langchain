import streamlit as st

from webui_pages.model_config.model_config import prompt_config_page
from webui_pages.utils import *
from streamlit_option_menu import option_menu
from webui_pages.dialogue.dialogue import dialogue_page, chat_box
from webui_pages.knowledge_base.knowledge_base import knowledge_base_page
import os
import sys
from configs import VERSION
from server.utils import api_address


api = ApiRequest(base_url=api_address())
if __name__ == "__main__":
    is_lite = "lite" in sys.argv

    st.set_page_config(
        "智能问答助手",
        os.path.join("img", "mechanical.png"),
        initial_sidebar_state="expanded",
        layout="wide",
        menu_items={
            'About': f"""欢迎使用 智能问答助手 {VERSION}！"""
        }
    )

    pages = {
        "对话": {
            "icon": "chat",
            "func": dialogue_page,
        },
        "提示词模板": {
            "icon": "file-earmark-text",
            "func": prompt_config_page,
        },
        "知识库管理": {
            "icon": "hdd-stack",
            "func": knowledge_base_page,
        },
    }

    with st.sidebar:
        st.image(
            os.path.join(
                "img",
                "mechanical.png"
            ),
            use_column_width='auto',
        )
        st.caption(
            f"""<p align="right">当前版本：{VERSION}</p>""",
            unsafe_allow_html=True,
        )
        options = list(pages)
        icons = [x["icon"] for x in pages.values()]

        default_index = 0
        selected_page = option_menu(
            "",
            options=options,
            icons=icons,
            # menu_icon="chat-quote",
            default_index=default_index,
        )

    if selected_page in pages:
        pages[selected_page]["func"](api=api, is_lite=is_lite)
