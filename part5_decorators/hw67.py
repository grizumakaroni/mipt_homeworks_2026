import json
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from functools import wraps
from typing import Any, ParamSpec, TypeVar
from urllib.request import urlopen

INVALID_CRITICAL_COUNT = "Breaker count must be positive integer!"
INVALID_RECOVERY_TIME = "Breaker recovery time must be positive integer!"
VALIDATIONS_FAILED = "Invalid decorator args."
TOO_MUCH = "Too much requests, just wait."
COMMENTS_URL_BASE = "https://jsonplaceholder.typicode.com/comments?postId="


P = ParamSpec("P")
R_co = TypeVar("R_co", covariant=True)


def validate_breaker_args(
    critical_count: int,
    time_to_recover: int,
) -> list[ValueError]:
    validation_errors: list[ValueError] = []
    if not isinstance(critical_count, int) or critical_count <= 0:
        validation_errors.append(ValueError(INVALID_CRITICAL_COUNT))
    if not isinstance(time_to_recover, int) or time_to_recover <= 0:
        validation_errors.append(ValueError(INVALID_RECOVERY_TIME))
    return validation_errors


class BreakerError(Exception):
    def __init__(self, *, func_name: str, block_time: datetime) -> None:
        super().__init__(TOO_MUCH)
        self.func_name = func_name
        self.block_time = block_time


class CircuitBreaker:
    def __init__(
        self,
        critical_count: int = 5,
        time_to_recover: int = 30,
        triggers_on: type[Exception] = Exception,
    ) -> None:
        validation_errors = validate_breaker_args(
            critical_count,
            time_to_recover,
        )
        if validation_errors:
            raise ExceptionGroup(VALIDATIONS_FAILED, validation_errors)

        self._critical_count = critical_count
        self._recover_delta = timedelta(seconds=time_to_recover)
        self._triggers_on = triggers_on
        self._failure_count = 0
        self._blocked_at: datetime | None = None

    def __call__(self, func: Callable[P, R_co]) -> Callable[P, R_co]:
        full_func_name = f"{func.__module__}.{func.__name__}"

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R_co:
            now = datetime.now(tz=UTC)
            self._maybe_raise_blocked(func_name=full_func_name, now=now)

            try:
                result = func(*args, **kwargs)
            except Exception as error:
                if isinstance(error, self._triggers_on):
                    self._on_trigger_exception(
                        func_name=full_func_name,
                        error=error,
                    )
                raise

            self._failure_count = 0
            return result

        return wrapper

    def _maybe_raise_blocked(self, *, func_name: str, now: datetime) -> None:
        if self._blocked_at is None:
            return
        if now - self._blocked_at >= self._recover_delta:
            self._blocked_at = None
            self._failure_count = 0
            return
        raise BreakerError(func_name=func_name, block_time=self._blocked_at)

    def _on_trigger_exception(
        self,
        *,
        func_name: str,
        error: Exception,
    ) -> None:
        self._failure_count += 1
        if self._failure_count < self._critical_count:
            return
        self._blocked_at = datetime.now(tz=UTC)
        raise BreakerError(
            func_name=func_name,
            block_time=self._blocked_at,
        ) from error


circuit_breaker = CircuitBreaker()


# @circuit_breaker
def get_comments(post_id: int) -> Any:
    """
    Получает комментарии к посту

    Args:
        post_id (int): Идентификатор поста

    Returns:
        list[dict[int | str]]: Список комментариев
    """
    open_url = urlopen
    response = open_url(f"{COMMENTS_URL_BASE}{post_id}")
    return json.loads(response.read())


if __name__ == "__main__":
    comments = get_comments(1)
