# Load test using Locust

We will try to compare our service working synchronously and asynchronously.

## Constant Incremental Load Test

We will test how the application behaves in high traffic times and we will find the architectures breaking points.

The test will submit several request (from 1 to 300) every second during 300 seconds.

### Sync

```
$ locust -f benchmark.py --host http://localhost:5001 --headless --users 300 --spawn-rate 1 --run-time 300s --html output/load_test_sync.html --csv=output/load_test_sync ApiSyncUser
```

<img width="1013" alt="Captura de pantalla 2023-09-30 a las 12 59 21" src="https://github.com/bukosabino/ia-boe/assets/4375209/9b2b7e35-bec8-431d-b47c-9908a17a0de5">

As you can see, 0.4 appears to be the maximum number of simultaneous requests per second that our synchronous architecture can properly manage.

At this point, the median response time is 9600ms.

If you had more than 0.4 requests per second, you would increase the response time, but you would have the same number of requests per second.

### Async

```
$ locust -f benchmark.py --host http://localhost:5001 --headless --users 300 --spawn-rate 1 --run-time 300s --html output/load_test_async.html --csv=output/load_test_async ApiAsyncUser
```

<img width="1013" alt="Captura de pantalla 2023-09-30 a las 12 59 54" src="https://github.com/bukosabino/ia-boe/assets/4375209/8fd19e1a-f6e5-477d-be21-274a4a8ef5b0">

As you can see, 12.1 seems to be the maximum number of simultaneous requests per second that our asynchronous architecture can properly manage.

At this point, the median response time is 5400ms.

If you have more requests than 12.1 per second, then you would increase the response time, but you will have the same number of requests per second.


**Notes:**

You can check the results on the `output` folder.
Based on [this example](https://github.com/bukosabino/scoring-handler/tree/main/benchmark/experiment3-benchmarking-locust)
