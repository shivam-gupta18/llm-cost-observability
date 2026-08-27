import time
import functools

from prometheus_client import Counter, Histogram

from observability.pricing import MODEL_PRICING
from observability.storage import log_call

LLM_CALLS_TOTAL = Counter("llm_calls_total", "Total LLM calls", ["model", "success"])
LLM_LATENCY_SECONDS = Histogram("llm_latency_seconds", "LLM call latency in seconds", ["model"])
LLM_COST_USD_TOTAL = Counter("llm_estimated_cost_usd_total", "Cumulative estimated cost (USD)", ["model"])
LLM_TOKENS_TOTAL = Counter("llm_tokens_total", "Total tokens processed", ["model", "direction"])


def estimate_cost(model, input_tokens, output_tokens):
    rates = MODEL_PRICING.get(model)
    if rates is None:
        return None
    cost = (input_tokens / 1_000_000) * rates["input"] + (output_tokens / 1_000_000) * rates["output"]
    return round(cost, 6)


def track(model_arg="model"):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            model = kwargs.get(model_arg, "unknown")
            start = time.monotonic()
            success = True
            error_msg = None
            input_tokens = output_tokens = 0
            response = None
            try:
                response = fn(*args, **kwargs)
                usage = getattr(response, "usage_metadata", None)
                if usage is not None:
                    input_tokens = getattr(usage, "prompt_token_count", 0) or 0
                    output_tokens = getattr(usage, "candidates_token_count", 0) or 0
                    if input_tokens == 0 and output_tokens == 0:
                        print(f"[observability] WARNING: usage_metadata present but "
                              f"token counts are 0 for model={model}: {usage!r}")
                else:
                    print(f"[observability] WARNING: no usage_metadata on response "
                          f"for model={model}; response type={type(response)}")
                return response
            except Exception as e:
                success = False
                error_msg = str(e)
                raise
            finally:
                latency_ms = (time.monotonic() - start) * 1000
                cost = estimate_cost(model, input_tokens, output_tokens)

                log_call(
                    model=model,
                    latency_ms=latency_ms,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    estimated_cost_usd=cost,
                    success=success,
                    error=error_msg,
                )

                LLM_CALLS_TOTAL.labels(model=model, success=str(success)).inc()
                LLM_LATENCY_SECONDS.labels(model=model).observe(latency_ms / 1000)
                if cost is not None:
                    LLM_COST_USD_TOTAL.labels(model=model).inc(cost)
                LLM_TOKENS_TOTAL.labels(model=model, direction="input").inc(input_tokens)
                LLM_TOKENS_TOTAL.labels(model=model, direction="output").inc(output_tokens)
        return wrapper
    return decorator
