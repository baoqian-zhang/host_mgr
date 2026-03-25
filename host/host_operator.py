from abc import ABC, abstractmethod


class HostOperator(ABC):

    @abstractmethod
    def ping(self, host):
        """检查 host 是否 ping 可达。"""

    @abstractmethod
    async def ping_async(self, host):
        """异步检查 host 是否 ping 可达。"""

    @abstractmethod
    def change_root_password(self, host, new_password):
        """在 host 上修改 root 密码。"""

    @abstractmethod
    async def change_root_password_async(self, host, new_password):
        """异步在 host 上修改 root 密码。"""


class HostOperatorAdapter(HostOperator):

    def ping(self, host):
        return True

    async def ping_async(self, host):
        return self.ping(host)

    def change_root_password(self, host, new_password):
        return True

    async def change_root_password_async(self, host, new_password):
        return self.change_root_password(host, new_password)
