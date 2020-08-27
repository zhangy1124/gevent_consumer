# coding=utf-8
import sys
import logging
import time

from confluent_kafka import Consumer, KafkaError
from consumer.retry_utils import retry

import gevent
from gevent import monkey
from gevent.event import Event
from gevent.queue import JoinableQueue as Queue
from gevent.hub import getcurrent
from gevent.signal import signal
from signal import SIGINT, SIGTERM

monkey.patch_all()  # noqa

logger = logging.getLogger(__name__)


class GeventConsumer(object):

    def __init__(
        self,
        consumer_config=None,
        topic=None,
        parse_func=None,
        num=8,
        auto_commit_offset=False,
        is_debug=False,
    ):
        if not parse_func:
            raise Exception("not parse func, system exit")

        self.parse = parse_func
        self.queue = Queue(100)
        self.stop_flag = Event()
        self.num = num
        self.debug = is_debug
        if not self.debug:
            self.auto_commit_offset = auto_commit_offset
            if isinstance(consumer_config, dict):
                consumer_config.update({'enable.auto.commit':self.auto_commit_offset})
            self.consumer = Consumer(consumer_config)
            self.topic = topic
            self.consumer.subscribe(self.topic)

    def sign_handler(self, sig, frame):
        print(" >>> Termination_signal:[{}] to stop".format(sig))
        self.stop_flag.set()

    def kafka_to_queue(self):
        logger.info("Start Producer thread")
        m = 0
        time_diff = 0
        start_time = time.time()
        while not self.stop_flag.is_set():
            msg = self.consumer.poll(1)
            if msg is None:
                time.sleep(0.001)
                return
            err = msg.error()
            if err:
                if err.code() == KafkaError._PARTITION_EOF:
                    logger.debug(
                        '%s [%s] reached end at offset %s',
                        msg.topic(), msg.partition(), msg.offset()
                    )
                else:
                    logger.error('kafka failed, system exit')
                    self.stop_flag.set()

            self.queue.put(msg)

            # 消费速度统计
            m += 1
            current_time = time.time()
            time_diff = current_time - start_time
            if time_diff > 10:
                rate = m / time_diff
                start_time = current_time
                m = 0
                logger.info('consumer_rate:[%.2f]p/s, queue_size:[%d]' % (rate, self.queue.qsize()))
        logger.info("Producer thread has stopped")

    def consume(self):
        logger.info('Start Thread To Consumer')
        data = dict()
        stop = False
        while True:
            stop = self.stop_flag.is_set()
            if stop and self.queue.empty():
                break
            msg = self.queue.get()
            try:
                data = self.parse(msg.value())
                if data:
                    self.handle_data(data, stop)
            finally:
                self.queue.task_done()
                if not stop and not self.auto_commit_offset:
                    self.consumer.commit(msg)
        logger.info('Thread Consumer has stopped')

    def handle_data(self, data, stop):
        raise NotImplementedError

    def consume_forever(self):
        """
        start consume forever
        """
        signal(SIGTERM, self.sign_handler)
        signal(SIGINT, self.sign_handler)

        if self.debug:
            consume_func = self.mock_consume
            produce_func = self.mock_kafka
        else:
            consume_func = self.consume
            produce_func = self.kafka_to_queue

        task_list = []
        for _ in range(self.num):
            task_list.append(gevent.spawn(consume_func))

        produce_func()
        self.queue.join()
        if not self.debug:
            logger.info("closing kafka...")
            self.consumer.close()
        gevent.joinall(task_list, timeout=5)
        logger.info('Exiting with qsize:%d' % self.queue.qsize())

    # ===========mock kafka and consumer=======================
    def mock_kafka(self):
        logger.info("Start Producer thread")
        m = 0
        time_diff = 0
        start_time = time.time()
        # jing5 msg
        msg = "23230254455354325631393046433232323232320101008e14080b0e0c38426e0101008422551354455354325631393046433232323232323131313131313131313131313131313131313131313131313131313131313131313130010000000002803365818a91eb00010002fffe050018fffe2eeb596f50830005e91efd02649c6b7eb1ac0d80000043c497fd0022f90a3d057b2403032581373635343332310082e99f008a06".decode('hex')
        while not self.stop_flag.is_set():
            self.queue.put(msg)
            m += 1

            # 消费速度统计
            current_time = time.time()
            time_diff = current_time - start_time
            if time_diff > 5:
                rate = m / time_diff
                start_time = current_time
                m = 0
                logger.info('consumer_rate:[%.2f]p/s, queue_size:[%d]' % (rate, self.queue.qsize()))
        logger.info("closing produce...")
        logger.info("Producer thread has stopped")

    def mock_consume(self):
        logger.info('Start Thread To Consumer')
        data = dict()
        stop = False
        while True:
            stop = self.stop_flag.is_set()
            if stop and self.queue.empty():
                break
            msg = self.queue.get()
            try:
                data = self.parse(msg)
                self.handle_data(data, stop)
            except Exception as err:
                logger.error("consumer:{}".format(getcurrent()))
            finally:
                self.queue.task_done()
        logger.info('Thread Consumer has stopped')
