from time import sleep
from huey import RedisHuey
from redis import StrictRedis
from prometheus_client import Gauge, start_http_server


class HueyExporter:
    def __init__(self, collect_interval: int, metrics_port: int, redis_host: str, redis_port: int) -> None:
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.metrics_port = metrics_port
        self.collect_interval = collect_interval
        self.huey = RedisHuey()
        self.queue_length_gauge = Gauge('queue_length', 'Current length of queue')
        self.redis_state_gauge = Gauge('redis_state', 'State of the Redis process (1=up, 0=down)')
        self.huey_state_gauge = Gauge('huey_state', 'State of the Huey process (1=up, 0=down)')

    def set_redis_state_gauge(self, value: bool) -> None:
        if value:
            self.redis_state_gauge.set(1)
        else:
            self.redis_state_gauge.set(0)

    def set_huey_state_gauge(self, value: bool) -> None:
        if value:
            self.huey_state_gauge.set(1)
        else:
            self.huey_state_gauge.set(0)

    def huey_up(self) -> bool:
        if self.huey.is_alive():
            return True
        return False

    def redis_up(self) -> bool:
        try:
            redis_instance = StrictRedis(host=self.redis_host, port=self.redis_port)
            redis_instance.ping()
            return True
        except:
            return False
        
    def collect_metrics(self) -> None:
        self.queue_length_gauge.set(self.huey.pending_count())
        self.set_redis_state_gauge(self.redis_up())
        self.set_huey_state_gauge(self.huey_up())

    def metric_collection_loop(self) -> None:
        while True:
            self.collect_metrics()
            sleep(self.collect_interval)

    def start_exporter(self) -> None:
        start_http_server(self.metrics_port)
        self.metric_collection_loop()


if __name__ == '__main__':
    huey_exporter = HueyExporter(15, 8887, 'localhost', 6379)
    huey_exporter.start_exporter()
