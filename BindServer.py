import os
import logging
from typing import List, Tuple
from plugins.base_plugin import BasePlugin
from auth_manager import auth_manager

class BindServerPlugin(BasePlugin):
    """
    SCP:SL服务器管理插件 - 管理员专用
    命令格式：/绑定服务器 [Add/Remove/Check] [ServerIP] [ServerPort]
    """
    
    def __init__(self):
        super().__init__(
            command="绑定服务器",
            description="SCP:SL服务器管理(仅限群管理)",
            is_builtin=True
        )
        self.save_dir = "ServerBindQQqun"
        os.makedirs(self.save_dir, exist_ok=True)
        self.logger = logging.getLogger("plugin.bind_server")
    
    async def handle(self, params: str, user_id: str = None, group_openid: str = None, **kwargs) -> str:
        try:
            # 检查权限和群聊环境
            if not auth_manager.is_admin(user_id):
               return "权限不足，此命令仅限管理员使用"
            
            # 解析参数
            parts = params.strip().split()
            if len(parts) < 1:
                return self._get_usage_help()
            
            mode = parts[0].lower()
            
            # 处理不同模式
            if mode == "add":
                if len(parts) != 3:
                    return "⚠️ 参数错误！格式：/绑定服务器 Add ServerIP ServerPort"
                return await self._add_server(group_openid, parts[1], parts[2])
            
            elif mode == "remove":
                if len(parts) != 3:
                    return "⚠️ 参数错误！格式：/绑定服务器 Remove ServerIP ServerPort"
                return await self._remove_server(group_openid, parts[1], parts[2])
            
            elif mode == "check":
                if len(parts) != 3:
                    return "⚠️ 参数错误！格式：/绑定服务器 Check ServerIP ServerPort"
                return await self._check_server(group_openid, parts[1], parts[2])
            
            elif mode == "list":
                return await self._list_servers(group_openid)
            
            else:
                return self._get_usage_help()
                
        except Exception as e:
            self.logger.error(f"操作失败: {str(e)}", exc_info=True)
            return "❌ 操作失败，请检查日志"

    async def _add_server(self, group_id: str, server_ip: str, server_port: str) -> str:
        """添加服务器信息"""
        file_path = os.path.join(self.save_dir, f"{group_id}.txt")
        servers = await self._load_servers(group_id)
        
        # 检查是否已存在
        for record in servers:
            if record[0] == server_ip and record[1] == server_port:
                return "ℹ️ 该服务器信息已存在"
        
        # 验证端口有效性
        try:
            port = int(server_port)
            if not (0 < port <= 65535):
                raise ValueError
        except ValueError:
            return "⚠️ 端口号必须为1-65535之间的整数"
        
        # 添加新记录
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(f"{server_ip} {server_port}\n")
        
        return f"✅ 已添加服务器\nIP: {server_ip}\n端口: {server_port}"

    async def _remove_server(self, group_id: str, server_ip: str, server_port: str) -> str:
        """移除服务器信息"""
        servers = await self._load_servers(group_id)
        new_servers = [r for r in servers if r[0] != server_ip or r[1] != server_port]
        
        if len(new_servers) == len(servers):
            return "ℹ️ 未找到匹配的服务器信息"
        
        file_path = os.path.join(self.save_dir, f"{group_id}.txt")
        with open(file_path, 'w', encoding='utf-8') as f:
            for record in new_servers:
                f.write(f"{record[0]} {record[1]}\n")
        
        return f"✅ 已移除服务器\nIP: {server_ip}\n端口: {server_port}"

    async def _check_server(self, group_id: str, server_ip: str, server_port: str) -> str:
        """检查服务器信息"""
        servers = await self._load_servers(group_id)
        exists = any(r[0] == server_ip and r[1] == server_port for r in servers)
        
        if exists:
            return f"🟢 服务器存在\nIP: {server_ip}\n端口: {server_port}"
        return f"🔴 服务器不存在\nIP: {server_ip}\n端口: {server_port}"

    async def _list_servers(self, group_id: str) -> str:
        """列出所有绑定的服务器"""
        servers = await self._load_servers(group_id)
        
        if not servers:
            return "ℹ️ 当前没有绑定的服务器"
        
        response = "📋 绑定的服务器列表:\n"
        for i, (ip, port) in enumerate(servers, 1):
            response += f"{i}. {ip}:{port}\n"
        
        return response.strip()

    async def _load_servers(self, group_id: str) -> List[Tuple[str, str]]:
        """加载服务器列表"""
        file_path = os.path.join(self.save_dir, f"{group_id}.txt")
        if not os.path.exists(file_path):
            return []
        
        servers = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    parts = line.split()
                    if len(parts) == 2:  # 必须包含IP和端口
                        servers.append((parts[0], parts[1]))
        return servers

    def _get_usage_help(self) -> str:
        """使用帮助"""
        return (
            "SCPSL服务器绑定命令使用指南：\n"
            "1. 添加服务器：/绑定服务器 Add <ServerIP> <ServerPort>\n"
            "2. 移除服务器：/绑定服务器 Remove <ServerIP> <ServerPort>\n"
            "3. 检查服务器：/绑定服务器 Check <ServerIP> <ServerPort>\n"
            "4. 列出服务器：/绑定服务器 List\n"
        )

    def help(self) -> str:
        return self._get_usage_help()