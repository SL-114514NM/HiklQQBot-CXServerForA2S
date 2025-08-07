import os
import asyncio
import a2s
import time
from typing import List, Dict, Tuple
from plugins.base_plugin import BasePlugin
from socket import gaierror

class QueryServerPlugin(BasePlugin):
    """
    SCP:SL服务器状态查询插件
    使用group_openid作为绑定文件标识
    """
    
    def __init__(self):
        super().__init__(
            command="CX",
            description="SCP:SL服务器状态检测",
            is_builtin=True
        )
        self.save_dir = "ServerBindQQqun"
        os.makedirs(self.save_dir, exist_ok=True)
        self.timeout = 5  # 查询超时时间(秒)

    async def handle(self, params: str = "", user_id: str = None, group_openid: str = None, **kwargs) -> str:
        # 检查必要的群聊ID
        if not group_openid:
            return "⚠️ 此功能仅限群聊使用"
        
        # 获取该群绑定的服务器列表
        servers = await self._load_servers(group_openid)
        if not servers:
            return "⚠️ 本群未绑定服务器\n使用/绑定服务器 Add [IP] [端口] 添加"

        # 并行查询所有服务器状态
        results = await asyncio.gather(
            *[self._check_server_status(ip, port) for ip, port in servers]
        )
        
        # 构建响应消息
        response = []
        for (ip, port), (online, ping, info) in zip(servers, results):
            if online:
                server_info = [
                    f"🟢 在线 [{ping}ms] {ip}:{port}",
                    f"  ▪ 名称: {info.server_name}",
                    f"  ▪ 地图: {info.map_name}",
                    f"  ▪ 玩家: {info.player_count}/{info.max_players}"
                ]
                response.append("\n".join(server_info))
            else:
                response.append(f"🔴 不在线 {ip}:{port}")

        return "\n\n".join(response) if response else "❌ 未获取到有效服务器信息"

    async def _check_server_status(self, ip: str, port: str) -> Tuple[bool, int, any]:
        """检测服务器状态返回(在线状态, 延迟ms, 基础信息)"""
        address = (ip, int(port)) if port.isdigit() else (ip, 27015)
        
        try:
            start = time.monotonic()
            info = await a2s.ainfo(address, timeout=self.timeout)
            return (True, int((time.monotonic() - start) * 1000), info)
        except (gaierror, asyncio.TimeoutError, a2s.BrokenMessageError):
            return (False, 9999, None)
        except Exception as e:
            print(f"查询异常: {type(e).__name__}: {str(e)}")
            return (False, 9999, None)

    async def _load_servers(self, group_openid: str) -> List[Tuple[str, str]]:
        """从群绑定文件加载服务器列表"""
        file_path = os.path.join(self.save_dir, f"{group_openid}.txt")
        if not os.path.exists(file_path):
            return []
        
        servers = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if parts := line.strip().split():
                    if len(parts) >= 2:  # 需要IP和端口两个参数
                        servers.append((parts[0], parts[1]))
        return servers

    def help(self) -> str:
        return (
            "📌 服务器状态查询命令: /CX\n"
            "返回本群绑定的所有服务器状态\n"
            "需要先使用绑定命令添加服务器:\n"
            "/绑定服务器 Add [IP] [端口]"
        )