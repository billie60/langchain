from .basic_config import *
from .kb_config import *
from .model_config import *
from .prompt_config import *
from .server_config import *

VERSION = "v0.1.0"
PROMPT_TEMPLATE_JSON = "configs/prompt_template.json"
# 获取项目根目录的绝对路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
