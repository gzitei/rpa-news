from functools import wraps
from status import STATUS


def job_status_handler(method) -> callable:
    @wraps(method)
    def wrapper(self, status, *args, **kwargs):
        if status == STATUS.SUCCESS:
            self.job_counter()
            method(self, status, *args, **kwargs)
            print("Job done!")
        elif status == STATUS.SYSTEM_ERROR:
            self.exception_counter()
            print("Job failed!")
        elif status == STATUS.BUSINESS_ERROR:
            self.exception_counter()
            method(self, status, *args, **kwargs)
            print("Job finished with error!")
        else:
            print("Unknown status!")
    return wrapper
