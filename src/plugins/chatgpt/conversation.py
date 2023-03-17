import json
from typing import Optional
from pathlib import Path


class Context:
    def __init__(self, path: Path, parent: 'Context' = None):
        self.path = path
        self.parent: Optional[Context] = parent
        self.system: list[str] = []
        self.load()

    def load(self):
        if not self.path.exists():
            return
        with self.path.open(encoding="UTF-8") as f:
            self.system = json.load(f)

    def save(self):
        with self.path.open("w", encoding="UTF-8") as f:
            json.dump(self.system, f)

    def get_system(self):
        return self.system

    def add_system(self, text: str) -> bool:
        if len(self.system) > 5 or len(text) > 50:
            return False
        self.system.append(text)
        self.save()
        return True

    def remove_system(self, pos: int) -> bool:
        if pos >= len(self.system):
            return False

        self.system.pop(pos)
        self.save()
        return True

    def get_messages(self):
        parent = []
        if self.parent is not None:
            parent = self.parent.get_messages()
        return parent + [{"role": "system", "content": m} for m in self.system]


class ContextUser(Context):
    def __init__(self, path: Path, parent: Context = None):
        super().__init__(path, parent)
        self.conversations: list[(str, str)] = []

    def push_conversation(self, question: str, response: str) -> None:
        self.conversations.append((question, response))
        if len(self.conversations) > 5:
            self.conversations.pop(0)

    def get_messages(self):
        result = super().get_messages()
        for question, response in self.conversations:
            result.append({"role": "user", "content": question})
            result.append({"role": "assistant", "content": response})
        return result

    def ask_with_context(self, question: str):
        result = self.get_messages()
        result.append({"role": "user", "content": question})
        return result


class ContextGroup(Context):
    def __init__(self, dir: Path):
        super().__init__(path=dir / "group.json")
        self.dir = dir
        self.dir.mkdir(exist_ok=True)
        self.users: dict[int, ContextUser] = dict()
        self.conversations: list[(str, str)] = []

    def get_user_context(self, uid: int) -> ContextUser:
        if uid in self.users:
            return self.users[uid]

        new_user = ContextUser(self.dir / f'{uid}.json', self)
        self.users[uid] = new_user
        return new_user


class ContextManager:
    def __init__(self):
        self.path = Path('data')
        self.path.mkdir(exist_ok=True)
        self.path_users = self.path / "users"
        self.path_users.mkdir(exist_ok=True)
        self.path_groups = self.path / "groups"
        self.path_groups.mkdir(exist_ok=True)
        self.users: dict[int, ContextUser] = dict()
        self.groups: dict[int, ContextGroup] = dict()

    def get_user_context(self, uid: int) -> ContextUser:
        if uid in self.users:
            return self.users[uid]

        new_user = ContextUser(path=self.path_users / f"{uid}.json")
        self.users[uid] = new_user
        return new_user

    def get_group_context(self, gid: int) -> ContextGroup:
        if gid in self.groups:
            return self.groups[gid]

        new_group = ContextGroup(dir=self.path_groups / f'{gid}')
        self.groups[gid] = new_group
        return new_group

    def get_group_user_context(self, gid: int, uid: int) -> ContextUser:
        return get_group_context(gid).get_user(uid)
