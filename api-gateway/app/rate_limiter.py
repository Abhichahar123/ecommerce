import redis
import time
import os
from fastapi import HTTPException, Request
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))

redis_client = redis.from_url(REDIS_URL, decode_responses=True)


def get_client_ip(request: Request) -> str:
    """
    Client ka IP address lo.
    Rate limiting IP pe based hogi — har IP ka alag limit.
    """
    # X-Forwarded-For → jab proxy/load balancer ke peeche ho
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host


def check_rate_limit(request: Request):
    """
    Sliding Window Rate Limiter.
    
    Har request pe:
    1. Client IP lo
    2. Redis mein check karo kitni requests aayi hain last 1 minute mein
    3. Limit se zyada → 429 error
    4. Limit ke andar → request allow karo, count badhao
    """
    client_ip = get_client_ip(request)
    
    # Redis key — har IP ka alag key
    key = f"rate_limit:{client_ip}"
    
    # Current timestamp (milliseconds mein)
    now = time.time()
    
    # 1 minute pehle ka timestamp
    window_start = now - 60
    
    # Pipeline → multiple Redis commands ek saath chalao (fast)
    pipe = redis_client.pipeline()
    
    # Purane requests remove karo (1 minute se pehle ke)
    pipe.zremrangebyscore(key, 0, window_start)
    
    # Current window mein kitni requests hain
    pipe.zcard(key)
    
    # Current request add karo
    pipe.zadd(key, {str(now): now})
    
    # Key ko 2 minutes mein expire karo (cleanup ke liye)
    pipe.expire(key, 120)
    
    # Sab commands ek saath execute karo
    results = pipe.execute()
    
    # Request count (zadd se pehle wala zcard result)
    request_count = results[1]
    
    print(f"IP: {client_ip} | Requests in last minute: {request_count + 1}/{RATE_LIMIT_PER_MINUTE}")
    
    # Limit check karo
    if request_count >= RATE_LIMIT_PER_MINUTE:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "message": f"Maximum {RATE_LIMIT_PER_MINUTE} requests per minute allowed",
                "retry_after": "60 seconds"
            }
        )