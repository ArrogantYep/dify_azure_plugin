from dify_plugin import Plugin, DifyPluginEnv
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 创建插件环境配置
plugin_env = DifyPluginEnv(
    MAX_REQUEST_TIMEOUT=120,
    INSTALL_METHOD=os.getenv('INSTALL_METHOD', 'remote'),
    REMOTE_INSTALL_HOST=os.getenv('REMOTE_INSTALL_HOST'),
    REMOTE_INSTALL_PORT=int(os.getenv('REMOTE_INSTALL_PORT', '5003')),
    REMOTE_INSTALL_KEY=os.getenv('REMOTE_INSTALL_KEY')
)

# 初始化插件
plugin = Plugin(plugin_env)

if __name__ == '__main__':
    try:
        plugin.run()
    except Exception as e:
        print(f"插件运行错误: {str(e)}")
