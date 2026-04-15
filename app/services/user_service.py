from app.repositories.user import UserRepository

class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def get_all_users(self):
        return self.user_repo.get_all_users()

    def disable_user(self, user_id: int) -> bool:
        user = self.user_repo.get_user_by_id(user_id)
        if not user:
            return False
        
        user.is_active = False
        self.user_repo.save(user)
        return True

    def enable_user(self, user_id: int) -> bool:
        user = self.user_repo.get_user_by_id(user_id)
        if not user:
            return False
        
        user.is_active = True
        self.user_repo.save(user)
        return True
