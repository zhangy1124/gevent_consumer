# Gevent Consumer

A tool of base consumer

## Prerequisites

- librdkafka >= 0.11.5

## Usage

``` python
from gevent_consumer.consumer import GeventConsumer
from gevent_consumer.retry.utils import retry

class Consumer(GeventConsumer):

    @retry
    self.handle_data(data, stop):
        do_something_work
```

## Tip

func retry is a forever try it decorate func
and ladder time(second) to sleep

and stop arg is a event flag set by system signal to stop
if stop is_set the kafka consumer offset will not commit
and the msg in queue will re_consumer in next start
