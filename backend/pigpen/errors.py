class DomainError(Exception):
    def __init__(self, code, message, status=422, details=None):
        super().__init__(message)
        self.code, self.message, self.status, self.details = code, message, status, details

    def body(self):
        return {"error": {"code": self.code, "message": self.message, "details": self.details}}
